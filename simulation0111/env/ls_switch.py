from . import Context, FloodPacket, Link, ControlPacket, Switch, HBSwitch, ControllerTrait
import networkx as nx
"""A collection of links state switches"""
class LinkStateSwitch (Switch):
  """Layer A switch for link state"""
  def __init__ (self, name, ctx):
    super(LinkStateSwitch, self).__init__(name, ctx)
    self.g = nx.Graph()
    self.g.add_node(self.name)
    self.controllers = set()
  
  @property
  def graph (self):
    return self.g

  def removeLink (self, link):
    if self.g.has_edge(link.a.name, link.b.name):
      self.g.remove_edge(link.a.name, link.b.name)
    if isinstance(link.a, ControllerTrait):
      self.controllers.add(link.a.name)
    if isinstance(link.b, ControllerTrait):
      self.controllers.add(link.b.name)
    if link.a.name not in self.g:
      self.g.add_node(link.a.name)
    if link.b.name not in self.g:
      self.g.add_node(link.b.name)
    #print "%f %s thinks controller should be %s"%(self.ctx.now, self.name, self.currentLeader)

  def updateRules (self, source, match_action_pairs):
      super(LinkStateSwitch, self).updateRules(source, match_action_pairs)


  def NotifyDown (self, link):
    #print "%f %s NotifyDown"%(self.ctx.now, self.name)
    self.removeLink(link)
    super(LinkStateSwitch, self).NotifyDown(link)

  def addLink (self, link):
    self.g.add_edge(link.a.name, link.b.name, link=link)
    if isinstance(link.a, ControllerTrait):
      self.controllers.add(link.a.name)
    if isinstance(link.b, ControllerTrait):
      self.controllers.add(link.b.name)
    #print "%f %s thinks controller should be %s"%(self.ctx.now, self.name, self.currentLeader)

  def NotifyUp (self, link):
    #print "%f %s NotifyUp"%(self.ctx.now, self.name)
    self.addLink(link)
    super(LinkStateSwitch, self).NotifyUp(link)

  def processControlMessage (self, link, source, packet):
    #print "%f %s CtrlMessage"%(self.ctx.now, self.name)
    if packet.dest_id == ControlPacket.AllCtrlId:
      if packet.message_type == ControlPacket.NotifyLinkUp:
        (switch, link) = packet.message
        self.addLink(link)
      elif packet.message_type == ControlPacket.NotifyLinkDown:
        (switch, link) = packet.message
        self.removeLink(link)
    return super(LinkStateSwitch, self).processControlMessage(link, source, packet)

class LSLeaderSwitch (LinkStateSwitch):
  """A switch which builds on the leader switch from above by adding a Layer B that
     is responsible for figuring out the current leader, and only allows changes 
     from the current leader"""
  def __init__ (self, name, ctx):
    super(LSLeaderSwitch, self).__init__(name, ctx)
    self.cpkt_id = 1
  
  def updateRules (self, source, match_action_pairs):
    if source != self.currentLeader:
      #packet = ControlPacket(self.cpkt_id, self.name, source, ControlPacket.NackUpdateRules, []) 
      self.Flood(None, packet)
      self.cpkt_id += 1
    else:
      super(LSLeaderSwitch, self).updateRules(source, match_action_pairs)

  @property
  def currentLeader (self):
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.g, c, self.name):
        return c #Find the first connected controller

class LSController (LinkStateSwitch, ControllerTrait):
  """Generic controller with link state based layer A"""
  def __init__ (self, name, ctx, address):
    super(LSController, self).__init__(name, ctx)
    self.cpkts_seen = set()
    self.switchboard = {
     ControlPacket.NotifySwitchUp: self.NotifySwitchUp,
     ControlPacket.NotifyLinkDown: self.NotifyLinkDown,
     ControlPacket.NotifyLinkUp: self.NotifyLinkUp,
     ControlPacket.PacketIn: self.PacketIn,
     ControlPacket.SwitchInformation: self.NotifySwitchInformation,
     ControlPacket.GetSwitchInformation: lambda p, s: self.processSwitchInformation(s),
     ControlPacket.NackUpdateRules: self.NotifyNackUpdate
    }
    self.cpkt_id = 0
  def Send (self, packet):
    super(LSController, self).Flood(None, packet)
  def receive (self, link, source, packet):
    if isinstance(packet, ControlPacket):
      # Received a control packet
      if packet.dest_id == ControlPacket.AllCtrlId or packet.dest_id == self.name:
        if (packet.src_id, packet.id) not in self.cpkts_seen:
          self.cpkts_seen.add((packet.src_id, packet.id))
          #print "%s received a control packet type %d"%(self.name, packet.message_type)
          self.processControlMessage(link, source, packet)
          delay = self.ctx.config.ControlLatency
          if packet.message_type in self.switchboard:
            self.ctx.schedule_task(delay, lambda: self.switchboard[packet.message_type](packet, packet.src_id, *packet.message))
            # Send out an acknowledgment for receiving this packet (don't add ACK types to the switchboard, that would be
            # bad
            p = ControlPacket(self.cpkt_id, self.name, packet.src_id, ControlPacket.ControlAck, [packet.id])
            #print p
            #print p.message_type
            self.sendControlPacket(p)
          elif  packet.message_type == ControlPacket.ControlAck:
            # Don't ack ack packets
            pass
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
  def NotifySwitchUp (self, pkt, source, switch):
    raise NotImplementedError
  def NotifyLinkDown (self, pkt, source, switch, link):
    raise NotImplementedError
  def NotifyLinkUp (self, pkt, source, switch, link):
    raise NotImplementedError
  def NotifySwitchInformation (self, pkt, source, switch, links):
    raise NotImplementedError
  def PacketIn(self, pkt, src, switch, source, packet):
    raise NotImplementedError
  def UnknownPacket(self, src, packet):
    print "%s unknown message type %s"%(self.name, packet) 
  def NotifyNackUpdate(self, src, packet):
    raise NotImplementedError
