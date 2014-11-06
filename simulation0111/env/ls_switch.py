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
    if source != self.currentLeader:
      #pass
      print "%f %s rejecting update from non-leader %s"%(self.ctx.now, self.name, source)
    else:
      super(LinkStateSwitch, self).updateRules(source, match_action_pairs)


  def NotifyDown (self, link):
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
    self.addLink(link)
    super(LinkStateSwitch, self).NotifyUp(link)

  def processControlMessage (self, link, source, packet):
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
  
  def updateRules (self, source, match_action_pairs):
    if source != self.currentLeader:
      #pass
      print "%f %s rejecting update from non-leader %s"%(self.ctx.now, self.name, source)
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
    self.switchboard = {
     ControlPacket.NotifySwitchUp: self.NotifySwitchUp,
     ControlPacket.NotifyLinkDown: self.NotifyLinkDown,
     ControlPacket.NotifyLinkUp: self.NotifyLinkUp,
     ControlPacket.PacketIn: self.PacketIn,
     ControlPacket.SwitchInformation: self.NotifySwitchInformation,
     ControlPacket.GetSwitchInformation: self.processSwitchInformation
    }
    self.cpkt_id = 0
  def Send (self, packet):
    super(LSController, self).Flood(None, packet)
  def receive (self, link, source, packet):
    if isinstance(packet, ControlPacket):
      # Received a control packet
      if packet.dest_id == ControlPacket.AllCtrlId or packet.dest_id == self.name:
        #print "%s received a control packet type %d"%(self.name, packet.message_type)
        self.processControlMessage(link, source, packet)
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

