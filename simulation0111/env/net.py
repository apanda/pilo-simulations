from . import Context, FloodPacket
"""
Network elements, because why not.
"""
class Link (object):
  """Represents a link, delays packets and calls receive on the other side"""
  def __init__ (self, ctx, ep1, ep2):
    self.ctx = ctx
    self.a = ep1
    self.b = ep2
    self.up = False
  def SetUp (self):
    if not self.up:
      self.up = True # Set link status to up
      delay = self.ctx.config.DetectionDelay
      self.ctx.schedule_task(delay, lambda: self.a.NotifyUp(self))
      self.ctx.schedule_task(delay, lambda: self.b.NotifyUp(self))
  def SetDown (self):
    if self.up:
      self.up = False # Set link status to down
      delay = self.ctx.config.DetectionDelay
      self.ctx.schedule_task(delay, lambda: self.a.NotifyDown(self))
      self.ctx.schedule_task(delay, lambda: self.b.NotifyDown(self))
  def Send (self, source, packet):
    assert source == self.a or source == self.b
    other = self.b
    if source == self.b:
      other = self.a
    def deliverInternal(link, source, dest, packet):
      if link.up:
        dest.receive(link, source, packet)
      else:
        print "Dropping packet for link from %s-%s"%(source, dest) #FIXME: Use logging
    delay = self.ctx.config.DataLatency
    self.ctx.schedule_task(delay, \
            lambda: deliverInternal(self, source, other, packet))

class Switch (object):
  """A simple match based switch, no link state update number"""
  def __init__ (self, name, ctx, controller):
    self.name = name
    self.ctx = ctx
    self.controller = controller
    self.rules = {}
    self.links = set()
  def __repr__ (self):
    return self.name
  def updateRules (self, match_action_pairs):
    delay = self.ctx.config.UpdateDelay
    self.ctx.schedule_task(delay, \
            lambda: self.rules.update(match_action_pairs))

  def anounceToController (self):
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay,
            lambda: self.controller.NotifySwitchUp(self))

  def Flood (self, link, packet):
    for l in self.links:
      if l is not link: 
        delay = self.ctx.config.SwitchLatency
        (lambda l1: self.ctx.schedule_task(delay, \
                lambda: l1.Send(self, packet)))(l)

  def receive (self, link, source, packet):
    match = packet.pack()
    packet.ttl -= 1
    if packet.ttl == 0:
      print "Dropping due to TTL"
      return
    if isinstance(packet, FloodPacket):
      print "Switch %s received flood %s"%(self.name, packet.id)
      self.Flood (link, packet)
      return
    if match in self.rules:
      delay = self.ctx.config.SwitchLatency
      self.ctx.schedule_task(delay, \
              lambda: self.rules[match].Send(self, packet))
    else:
      delay = self.ctx.config.ControlLatency
      self.ctx.schedule_task(delay, \
              lambda: self.controller.PacketIn(self, source, packet))
  
  def ForwardPacket (self, link, packet):
    delay = self.ctx.config.SwitchLatency
    self.ctx.schedule_task(delay, \
            lambda: link.Send(self, packet))

  def NotifyDown (self, link):
    self.links.remove(link)
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay, \
            lambda: self.controller.NotifyLinkDown(self, link))

  def NotifyUp (self, link):
    self.links.add(link)
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay, \
            lambda: self.controller.NotifyLinkUp(self, link))

class Host (Switch):
  def __init__ (self, name, ctx, controller, address):
    super(Host, self).__init__(name, ctx, controller)
    self.address = address

  def receive (self, link, source, packet):
    print "Received from %s %s"%(source.name, str(packet))

  def Send (self, packet):
    super(Host, self).Flood(None, packet)

class VersionedSwitch (Switch):
  def __init__ (self, name, ctx, controller):
    self.version = 0
    super(VersionedSwitch, self).__init__(name, ctx, controller)

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

class Controller (object):
  """Base class for controllers"""
  def __init__ (self, ctx):
    self.ctx = ctx
  def ForwardPacket (self, switch, link, packet):
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay, lambda: switch.ForwardPacket(link, packet))
  def UpdateRules (self, switch, pairs):
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay, lambda: switch.updateRules(pairs))
  def NotifySwitchUp (self, switch):
    raise NotImplementedError
  def NotifyLinkDown (self, switch, link):
    raise NotImplementedError
  def NotifyLinkUp (self, switch, link):
    raise NotImplementedError
  def PacketIn(self, switch, source, packet):
    raise NotImplementedError

