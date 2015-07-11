from . import Context, FloodPacket, Link, ControlPacket, ControllerTrait, ConnectionManager
class Switch (object):
  """A simple match based switch, with no layer A functionality."""
  RETRY_INTERVAL = 100
  def __init__ (self, name, ctx):
    self.name = name
    self.ctx = ctx
    self.rules = {}
    self.links = set()
    self.ctrl_messages = set()
    # A control notification is unacked as long as at least one controller hasn't seen it.
    self.unacked_ctrl = {}
    # This is a hack to avoid flooding infinitely since I don't want to implement
    # spanning tree. This is a bad hack to put in, but I am lazy.
    self.flooded_pkts = set()
    self.rule_change_notification = None
    self.cpkt_id = 0
    self.drop_callback = None
    self.ctrl_switchboard = {
      ControlPacket.UpdateRules: self.updateRules,
      ControlPacket.ForwardPacket: self.forwardPacket,
      ControlPacket.ControlAck: self.ackControl
    }
    self.conn_man = ConnectionManager(self)
    self.anounceToController()

  def __repr__ (self):
    return self.name

  def sendToController (self, type, args, controller = None):
    self.floodToController (type, args, controller)

  def floodToController (self, type, args, controller = None):
    """For now flood and send to all controllers, in some sense
       all controllers need to correctly update their view, etc."""
    if not controller:
      controller = ControlPacket.AllCtrlId
    p = ControlPacket(self.cpkt_id, self.name, controller, type, args)
    self.cpkt_id += 1
    self.Flood(None, p)

  def ackControl (self, source, id):
    # Remove id
    if id in self.unacked_ctrl:
      del self.unacked_ctrl[id]

  def relSend (self, id, p):
    self.unacked_ctrl[id] = p
    self.Flood(None, p)
    self.ctx.schedule_task(Switch.RETRY_INTERVAL, 
                             lambda: self.retryControlSend(id))

  def floodToControllerReliable (self, type, args, controller = None):
    """For now flood and send to all controllers, in some sense
       all controllers need to correctly update their view, etc."""
    if not controller:
      controller = ControlPacket.AllCtrlId
    p = ControlPacket(self.cpkt_id, self.name, controller, type, args)
    self.relSend(self.cpkt_id, p)
    self.cpkt_id += 1

  def retryControlSend (self, id):
    if id in self.unacked_ctrl:
      self.relSend(id, self.unacked_ctrl[id])

  def newControllerRule(self, controller, link):
    pass

  def updateRules (self, source, dest_action_pairs):
    print "Updating rules for %s"%(dest_action_pairs)
    match_action_pairs = []
    for (r, l) in dest_action_pairs:
      match_action_pairs.append((r.name, l))
      if isinstance(r, ControllerTrait):
        self.newControllerRule(r, l)
    if self.rule_change_notification:
      for (r, l) in match_action_pairs:
        if r not in self.rules or l != self.rules[r]:
          self.rule_change_notification(self.name)
    self.rules.update(match_action_pairs)
  
  def processSwitchInformation (self, source):
    p = ControlPacket(self.cpkt_id, \
            self.name, \
            source, \
            ControlPacket.SwitchInformation, \
            [self, \
              map(lambda l: (l.version, l), list(self.links))])
    self.cpkt_id += 1
    self.Flood(None, p)

  def anounceToController (self):
    # Does not make sense to do this through not flooding.
    self.floodToControllerReliable(ControlPacket.NotifySwitchUp, [self])

  def Flood (self, link, packet):
    for l in self.links:
      if l is not link: 
        delay = self.ctx.config.SwitchLatency
        (lambda l1: self.ctx.schedule_task(delay, \
                lambda: l1.Send(self, packet)))(l)

  def processControlMessage (self, packet):
    """Process message and decide whether to flood or not"""
    if packet.message_type == ControlPacket.GetSwitchInformation:
      if packet not in self.ctrl_messages:
        self.ctrl_messages.add(packet)
        self.processSwitchInformation(packet.src_id)
    if packet.dest_id == self.name: # Note not validating leader here
      if packet not in self.ctrl_messages:
        self.ctrl_messages.add(packet)
        if packet.message_type in self.ctrl_switchboard:
          self.ctrl_switchboard[packet.message_type](packet.src_id, *packet.message)
      return False # Processed, no point in processing again
    return True

  def receive (self, packet):
    if isinstance(packet, ControlPacket):
      print "Received control packet"
      self.processControlMessage(packet)

  def phy_receive (self, link, source, packet):
    packet.ttl -= 1
    packet.path.append(self.name)
    if packet.ttl == 0:
      #print "%f Dropping due to TTL %s %s"%(self.ctx.now, packet, type(packet))
      return
    if isinstance(packet, ControlPacket):
      if not self.processControlMessage(packet):
        return # Ensuring no flooding
    if isinstance(packet, FloodPacket):
      if packet not in self.flooded_pkts:
        #print "%f %s flooding %s %s"%(self.ctx.now, self.name, packet, type(packet))
        self.flooded_pkts.add(packet)
        self.Flood (link, packet)
      return
    if isinstance(packet, ConnectionManager) and packet.destination == self.name:
      self.conn_man.ReceivePacket(packet)
      return
    # Switch to destination based rules
    match = packet.destination
    if match in self.rules:
      delay = self.ctx.config.SwitchLatency
      self.ctx.schedule_task(delay, \
              lambda: self.rules[match].Send(self, packet))
    else:
      self.NotifyDrop (source, packet)
      self.sendToController(ControlPacket.PacketIn, [self, source, packet])

  def Send (self, packet):
    match = packet.destination
    if match in self.rules:
      delay = self.ctx.config.SwitchLatency
      link = self.rules[match]
      self.ctx.schedule_task(delay, lambda: link.Send(self, packet))
      return True
    return False

  def NotifyDrop (self, source, packet):
    # Dropping packet
    if self.drop_callback:
      self.drop_callback(self, source, packet)
  
  def forwardPacket (self, link, packet):
    delay = self.ctx.config.SwitchLatency
    self.ctx.schedule_task(delay, \
            lambda: link.Send(self, packet))

  def NotifyDown (self, link, version):
    self.links.remove(link)
    self.sendToController(ControlPacket.NotifyLinkDown, [version, self, link])

  def NotifyUp (self, link, first_up, version):
    self.links.add(link)
    # Notify if up after failure
    #if not first_up:
    self.sendToController(ControlPacket.NotifyLinkUp, [version, self, link])
