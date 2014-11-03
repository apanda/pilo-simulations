from . import Context, FloodPacket, Host, ControlPacket
"""
Network elements, because why not.
"""
class Controller (Host):
  """Base class for controllers"""
  def __init__ (self, name, ctx, address):
    super(Controller, self).__init__(name, ctx, address)
    self.switchboard = {
     ControlPacket.NotifySwitchUp: self.NotifySwitchUp,
     ControlPacket.NotifyLinkDown: self.NotifyLinkDown,
     ControlPacket.NotifyLinkUp: self.NotifyLinkUp,
     ControlPacket.PacketIn: self.PacketIn
    }
    self.cpkt_id = 0
  def receive (self, link, source, packet):
    if isinstance(packet, ControlPacket):
      # Received a control packet
      if packet.dest_id == ControlPacket.AllCtrlId or packet.dest_id == self.name:
        print "%s received a control packet type %d"%(self.name, packet.message_type)
        if packet.message_type in self.switchboard:
          delay = self.ctx.config.ControlLatency
          self.ctx.schedule_task(delay, lambda: self.switchboard[packet.message_type](*packet.message))
        else:
         print "%s unknown message type %d"%(self.name, packet.message_type) 
  def ForwardPacket (self, switch, link, packet):
    delay = self.ctx.config.ControlLatency
    cpacket = ControlPacket(self.cpkt_id, self.name, switch.name, ControlPacket.ForwardPacket, [link, packet]) 
    self.cpkt_id += 1
    self.ctx.schedule_task(delay, lambda: self.send(cpacket))
  def UpdateRules (self, switch, pairs):
    print "Considering updating rules"
    delay = self.ctx.config.ControlLatency
    print "Delay is %f"%(delay)
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.UpdateRules, [pairs]) 
    self.cpkt_id += 1
    def Send():
      print "Actually sending rule update to %s"%(switch)
      self.Send(cpacket)
    self.ctx.schedule_task(delay, Send)
  def NotifySwitchUp (self, switch):
    raise NotImplementedError
  def NotifyLinkDown (self, switch, link):
    raise NotImplementedError
  def NotifyLinkUp (self, switch, link):
    raise NotImplementedError
  def PacketIn(self, switch, source, packet):
    raise NotImplementedError

