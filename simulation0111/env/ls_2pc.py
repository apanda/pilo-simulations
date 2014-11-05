from . import LSController, ControlPacket, LSLeaderSwitch
import networkx as nx

class LS2PCController (LSController):
  """Base class for controllers that do some form of 2PC on top of link state"""
  def __init__ (self, name, ctx, address):
    super(LS2PCController, self).__init__(name, ctx, address)
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

class LS2PCSwitch (LSLeaderSwitch):
  """Base class for controller that does 2PC on top of link state"""
  def __init__ (self, name, ctx):
    super(LS2PCSwitch, self).__init__(name, ctx)
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
