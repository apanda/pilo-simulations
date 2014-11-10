from . import LSController, ControlPacket, LSLeaderSwitch
import networkx as nx

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

class LS2PCController (LSController):
  """Base class for controllers that do some form of 2PC on top of link state"""
  def __init__ (self, name, ctx, address):
    super(LS2PCController, self).__init__(name, ctx, address)
    self.switchboard[ControlPacket.AckSetSwitchLeader] = self.NotifyAckSetSwitchLeader
    self.switchboard[ControlPacket.RequestRelinquishLeadership] = self.NotifyRequestRelinquishLeadership
    self.switchboard[ControlPacket.AckRelinquishLeadership] = self.NotifyAckRelinquishLeadership
    self.currently_leader_for = set()
    self.outstanding_request_for_switch = {}

  def SetSwitchLeadership (self, switch, controller):
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.SetSwitchLeader, [controller]) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)

  def ShouldBeCurrentLeader(self, switch):
    raise NotImplementedError
  
  def NewlyAppointedLeader (self, src):
    raise NotImplementedError

  def NewlyRemovedLeader (self, src):
    raise NotImplementedError

  def NotifyAckSetSwitchLeader(self, pkt, src, success, current_controller):
    if current_controller == self.name and src not in self.currently_leader_for:
      # Successfully became leader
      print "%f %s is now leader for %s"%(self.ctx.now, self.name, src)
      self.currently_leader_for.add(src)
      self.NewlyAppointedLeader(src)
    elif success and src in self.currently_leader_for:
      # Successfully left leadership
      self.currently_leader_for.remove(src)
      # Ack any outstanding requests to relinquish leadership
      if src in self.outstanding_request_for_switch:
        dest = self.outstanding_request_for_switch[src]
        del self.outstanding_request_for_switch[src]
        self.ackRequestRelinquish(dest, src, True)
      self.NewlyRemovedLeader (src)
    elif not success and \
            self.ShouldBeCurrentLeader(src) == self.name and\
            src not in self.currently_leader_for: # We should still be controller
      # Ask current controller to relinquish
      self.maybeRequestRelinquishing(current_controller, src)

  def NotifyRequestRelinquishLeadership (self, pkt, src, switch, other_controller):
    if switch not in self.currently_leader_for:
      self.ackRequestRelinquish(src, switch, False)
    elif self.ShouldBeCurrentLeader(switch) == self.name:
      # Am leader, should be leader, don't give up
      self.ackRequestRelinquish(src, switch, False)
    else:
      # Am leader, should not be leader, let the other person take over
      if switch in self.outstanding_request_for_switch and \
              self.outstanding_request_for_switch[switch] != src:
        # Only one of these should win, blindly let newer request win
        self.ackRequestRelinquish(self.outstanding_request_for_switch[switch], switch, False)
        self.outstanding_request_for_switch[switch] = src
      else:
        # No one has requested yet, send a request
        self.outstanding_request_for_switch[switch] = src
        self.SetSwitchLeadership(switch, "")

  def NotifyAckRelinquishLeadership (self, pkt, src, switch, success):
    if success or switch in self.currently_leader_for:
      # Woohoo, they relinquished, let us ask for leadership
      self.SetSwitchLeadership(switch, self.name)
    elif self.ShouldBeCurrentLeader(switch) == self.name and switch not in self.currently_leader_for:
      # Failed, but we should still be leader. Might have failed since
      # the old leader is no longer the leader, so start from the beginning
      self.SetSwitchLeadership(switch, self.name)

  def maybeRequestRelinquishing (self, current_controller, switch):
    """Send a request for current_controller to relinquish control of switch 
      if connect we think it is connected to the switch (and hence to us), otherwise
      just send the switch a request to set leadership"""
    if current_controller in self.graph and \
      nx.has_path(self.graph, current_controller, switch):
      # Is connected (and we think we should be leader, so we are also connected to
      # the switch and controller)
      cpacket = ControlPacket(self.cpkt_id, \
                              self.name,\
                              current_controller,\
                              ControlPacket.RequestRelinquishLeadership,\
                              [switch, self.name]) 
      self.cpkt_id += 1
      self.sendControlPacket(cpacket)
    else:
      # Is not connected so just ask switch
      self.SetSwitchLeadership(switch, self.name)


  def ackRequestRelinquish (self, dest, switch, success):
      cpacket = ControlPacket(self.cpkt_id, \
                              self.name,\
                              dest,\
                              ControlPacket.AckRelinquishLeadership,\
                              [switch, success]) 
      self.cpkt_id += 1
      self.sendControlPacket(cpacket)
    
