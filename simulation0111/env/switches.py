from . import Context, FloodPacket, Link, ControlPacket
"""
Network elements, because why not.
"""
class Switch (object):
  """A simple match based switch, no link state update number"""
  def __init__ (self, name, ctx):
    self.name = name
    self.ctx = ctx
    # self.controller = controller
    self.rules = {}
    self.links = set()
    self.ctrl_messages = set()
    # This is a hack to avoid flooding infinitely since I don't want to implement
    # spanning tree. This is a bad hack to put in, but I am lazy.
    self.flooded_pkts = set()
    self.cpkt_id = 0

  def __repr__ (self):
    return self.name

  def sendToController (self, type, args):
    """For now flood and send to all controllers, in some sense
       all controllers need to correctly update their view, etc."""
    p = ControlPacket(self.cpkt_id, self.name, ControlPacket.AllCtrlId, type, args)
    self.cpkt_id += 1
    self.Flood(None, p)

  def updateRules (self, match_action_pairs):
    delay = self.ctx.config.UpdateDelay
    self.ctx.schedule_task(delay, \
            lambda: self.rules.update(match_action_pairs))

  def anounceToController (self):
    #print "%s anouncing to controller switch up"%(self.name)
    self.sendToController(ControlPacket.NotifySwitchUp, [self])

  def Flood (self, link, packet):
    for l in self.links:
      if l is not link: 
        delay = self.ctx.config.SwitchLatency
        (lambda l1: self.ctx.schedule_task(delay, \
                lambda: l1.Send(self, packet)))(l)

  def processControlMessage (self, link, source, packet):
    """Process message and decide whether to floor or not"""
    if packet.message_type == ControlPacket.UpdateRules:
      if packet.dest_id == self.name: # Note not validating leader here
        if packet not in self.ctrl_messages:
          self.ctrl_messages.add(packet)
          self.updateRules(*packet.message)
        return False # Processed, no point in processing again
    elif packet.message_type == ControlPacket.ForwardPacket:
      if packet.dest_id == self.name: # Note not validating leader here
        if packet not in self.ctrl_messages:
          self.ctrl_messages.add(packet)
          self.updateRules(*packet.message)
        self.ForwardPacket(*packet.message)
        return False # Processed, no point in processing again
    return True

  def receive (self, link, source, packet):
    packet.ttl -= 1
    if packet.ttl == 0:
      print "Dropping due to TTL"
      return
    if isinstance(packet, ControlPacket):
      if not self.processControlMessage(link, source, packet):
        return # Ensuring no flooding
    if isinstance(packet, FloodPacket):
      #print "Switch %s received flood %s"%(self.name, packet.id)
      if packet not in self.flooded_pkts:
        self.flooded_pkts.add(packet)
        self.Flood (link, packet)
      return
    match = packet.pack()
    if match in self.rules:
      delay = self.ctx.config.SwitchLatency
      self.ctx.schedule_task(delay, \
              lambda: self.rules[match].Send(self, packet))
    else:
      self.sendToController(ControlPacket.PacketIn, [self, source, packet])
  
  def ForwardPacket (self, link, packet):
    delay = self.ctx.config.SwitchLatency
    self.ctx.schedule_task(delay, \
            lambda: link.Send(self, packet))

  def NotifyDown (self, link):
    self.links.remove(link)
    self.sendToController(ControlPacket.NotifyLinkDown, [self, link])

  def NotifyUp (self, link):
    self.links.add(link)
    self.sendToController(ControlPacket.NotifyLinkUp, [self, link])

class VersionedSwitch (Switch):
  def __init__ (self, name, ctx):
    self.version = 0
    super(VersionedSwitch, self).__init__(name, ctx)

  def updateRules (self, (version, match_action_pairs)):
    if version >= self.version:
      self.version = version
      super(VersionedSwitch, self).updateRules(match_action_pairs)

  def anounceToController (self):
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay,
            lambda: self.controller.NotifySwitchUp((self.version, self)))

  def NotifyDown (self, link):
    self.version += 1
    super(VersionedSwitch, self).NotifyDown((self.version, link))

  def NotifyUp (self, link):
    self.version += 1
    super(VersionedSwitch, self).NotifyUp((self.version, link))

