from . import Context, HBSwitch

class HBLeaderSwitch (HBSwitch):
  """A switch with a Layer B added on to the heart beat switch. The layer B in this
  case just computes leaders locally and rejects changes not from the leader"""
  def __init__ (self, name, ctx, epoch, send_rate):
    super(HBLeaderSwitch, self).__init__(name, ctx, epoch, send_rate)
    self.leader = None

  @property
  def currentLeader(self):
    return self.leader
  
  def UpdatedConnectivity(self):
    """Deal with the fact that things have been updated. Currently
      just appoint the most connected, lowest ID controller leader"""
    super(HBLeaderSwitch, self).UpdatedConnectivity()
    connectivity_measure = sorted(map(lambda c: (-1 * len(self.connectivityMatrix.get(c, [])), c), self.controllers))
    if len(connectivity_measure) > 0 and \
       connectivity_measure[0][0] != 0 and \
       self.leader != connectivity_measure[0][1]: # Things are connected, etc.
      self.leader = connectivity_measure[0][1]
      #print "%f %s Setting %s as leader"%(self.ctx.now, self.name, self.currentLeader)

  def updateRules (self, source, match_action_pairs):
    if source != self.currentLeader:
      #print "%f %s rejecting update from non-leader %s"%(self.ctx.now, self.name, source)
      pass
    else:
      super(HBLeaderSwitch, self).updateRules(source, match_action_pairs)
