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
     ControlPacket.PacketIn: self.PacketIn,
     ControlPacket.SwitchInformation: self.NotifySwitchInformation,
     ControlPacket.GetSwitchInformation: self.processSwitchInformation
    }
    self.cpkt_id = 0
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

class LinkState2PCController (Controller):
  """Base class for controllers that do some form of 2PC"""
  def __init__ (self, name, ctx, address):
    super(LinkState2PCController, self).__init__(name, ctx, address)
    self.switchboard[ControlPacket.AckSetSwitchLeader] = self.NotifyAckSetSwitchLeader
    self.switchboard[ControlPacket.RequestRelinquishLeadership] = self.NotifyRequestRelinquishLeadership
    self.switchboard[ControlPacket.AckRelinquishLeadership] = self.NotifyAckRelinquishLeadership
  def SetSwitchLeadership (self, switch, controller):
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.SetSwitchLeader, [controller]) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)
  def NotifyAckSetSwitchLeader(self, src, success, current_controller):
    raise NotImplementedError
  def NotifyRequestRelinquishLeadership (self, src, switch, other_controller):
    raise NotImplementedError
  def NotifyAckRelinquishLeadership (self, src, switch, success):
    raise NotImplementedError
