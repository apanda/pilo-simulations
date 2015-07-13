from . import Context, FloodPacket, Host, ControlPacket, ControllerTrait
class Controller (Host, ControllerTrait):
  """No layer A controller"""
  def __init__ (self, name, ctx, address):
    super(Controller, self).__init__(name, ctx, address)
    self.switchboard = {
     ControlPacket.NotifySwitchUp: self.NotifySwitchUp,
     ControlPacket.NotifyLinkDown: self.NotifyLinkDown,
     ControlPacket.NotifyLinkUp: self.NotifyLinkUp,
     ControlPacket.PacketIn: self.PacketIn,
     ControlPacket.SwitchInformation: self.NotifySwitchInformation,
     ControlPacket.GetSwitchInformation: self.processSwitchInformation
    }
    self.cpkt_id = 0
    self.ctrl_callback = None
  def receive (self, link, source, packet):
    if isinstance(packet, ControlPacket):
      # Received a control packet
      if packet.dest_id == ControlPacket.AllCtrlId or packet.dest_id == self.name:
        #print "%s received a control packet type %d"%(self.name, packet.message_type)
        if packet.message_type in self.switchboard:
          delay = self.ctx.config.ControlLatency
          self.ctx.schedule_task(delay, lambda: self.switchboard[packet.message_type](packet.src_id, *packet.message))
        else:
          self.UnknownPacket(source, packet)
  def sendControlPacket(self, packet):
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay, lambda: self.Send(packet))
  def ForwardPacket (self, switch, link, packet):
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.ForwardPacket, [link, packet]) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)
  def UpdateRules (self, switch, pairs):
    print "%f sending update message with type %d and len %d"%(self.ctx.now, ControlPacket.UpdateRules, len(pairs))
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.UpdateRules, [pairs]) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)
  def GetSwitchInformation (self):
    cpacket = ControlPacket(self.cpkt_id, self.name, ControlPacket.AllCtrlId, ControlPacket.GetSwitchInformation, []) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)
  def NotifySwitchUp (self, source, switch):
    raise NotImplementedError
  def NotifyLinkDown (self, source, switch, link):
    raise NotImplementedError
  def NotifyLinkUp (self, source, switch, link):
    raise NotImplementedError
  def NotifySwitchInformation (self, source, switch, links):
    raise NotImplementedError
  def PacketIn(self, src, switch, source, packet):
    raise NotImplementedError
  def UnknownPacket(self, src, packet):
    print "%s unknown message type %d"%(self.name, packet.message_type) 
