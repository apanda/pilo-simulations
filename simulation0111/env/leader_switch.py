from . import Context, FloodPacket, Link, ControlPacket, Controller, Switch
import networkx as nx

class LeaderComputingSwitch (Switch):
  """This should be a subclass of versioned switch since it makes sense that
     a switch which is powerful enough to figure out who the leader is
     also rejects updates with bad link versions (I think). However, doing this
     requires writing a new controller and I am lazy for now.
     Also the leader computation protocol here is really simple, but bleh."""
  def __init__ (self, name, ctx):
    super(LeaderComputingSwitch, self).__init__(name, ctx)
    self.g = nx.Graph()
    self.g.add_node(self.name)
    self.controllers = set()
  
  def removeLink (self, link):
    self.g.remove_edge(link.a.name, link.b.name)
    if isinstance(link.a, Controller):
      self.controllers.add(link.a.name)
    if isinstance(link.b, Controller):
      self.controllers.add(link.b.name)
    #print "%f %s thinks controller should be %s"%(self.ctx.now, self.name, self.currentLeader)

  def updateRules (self, source, match_action_pairs):
    if source != self.currentLeader:
      #pass
      print "%f %s rejecting update from non-leader %s"%(self.ctx.now, self.name, source)
    else:
      super(LeaderComputingSwitch, self).updateRules(source, match_action_pairs)


  def NotifyDown (self, link):
    self.removeLink(link)
    super(LeaderComputingSwitch, self).NotifyDown(link)

  def addLink (self, link):
    self.g.add_edge(link.a.name, link.b.name)
    if isinstance(link.a, Controller):
      self.controllers.add(link.a.name)
    if isinstance(link.b, Controller):
      self.controllers.add(link.b.name)
    #print "%f %s thinks controller should be %s"%(self.ctx.now, self.name, self.currentLeader)

  def NotifyUp (self, link):
    self.addLink(link)
    super(LeaderComputingSwitch, self).NotifyUp(link)

  @property
  def currentLeader (self):
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.g, c, self.name):
        return c #Find the first connected controller

  def processControlMessage (self, link, source, packet):
    if packet.dest_id == ControlPacket.AllCtrlId:
      if packet.message_type == ControlPacket.NotifyLinkUp:
        (switch, link) = packet.message
        self.addLink(link)
      elif packet.message_type == ControlPacket.NotifyLinkDown:
        (switch, link) = packet.message
        self.removeLink(link)
    return super(LeaderComputingSwitch, self).processControlMessage(link, source, packet)

class LinkState2PCSwitch (LeaderComputingSwitch):
  """Just a version of the previous switch where we require explicit leadership changes"""
  def __init__ (self, name, ctx):
    super(LinkState2PCSwitch, self).__init__(name, ctx)
    self.current_leader = None
    self.ctrl_switchboard[ControlPacket.SetSwitchLeader] = self.processSetSwitchLeader
  
  @property
  def currentLeader (self):
    return self.current_leader
  
  @property
  def connectedToLeader (self):
    if self.current_leader is None:
      return False
    else:
      return nx.has_path(self.g, self.current_leader, self.name)

  def processSetSwitchLeader (self, src_id, controller):
    success = False
    if not self.current_leader:
      # Trivial case, no one is leader, people have correctly withdrawn.
      # Note: this isn't checking who the leader should be, should we be 
      # checking???
      self.current_leader = controller
      success = True
    elif controller == "" and src_id == self.current_leader:
      # Current leader is withdrawing.
      self.current_leader = None
      success = True
    elif not self.connectedToLeader:
      self.current_leader = controller
      success = True
    self.sendToController(ControlPacket.AckSetSwitchLeader, [success, self.current_leader], controller = src_id)
