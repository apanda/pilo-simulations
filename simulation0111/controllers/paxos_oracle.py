from env import Singleton
from sim import Simulation
import networkx as nx

class PaxosOracle (object):
  __metaclass__ = Singleton
  def __init__ (self):
    self.simulation = Simulation()
    self.proposed = []
    self.accepted = {}
    self.proposal_count = 0
    self.registered_controllers = {}
    self.already_proposed = set()
    self.already_accepted = set()
    self.proposers = {}
    self.prop_count = {}
  
  def Reset (self):
    self.simulation = Simulation()
    self.proposed = []
    self.accepted = {}
    self.proposal_count = 0
    self.registered_controllers = {}
    self.already_proposed = set()
    self.already_accepted = set()
    self.proposers = {}
    self.prop_count = {}
  
  def CheckConnectivity (self, controller):
    """Check if a majority of controllers are connected and if
        the named controller is a part of this group."""
    components = nx.connected_components(self.simulation.graph)
    # Find the component containing the controller
    component = filter(lambda c: controller in c, components)[0]
    connected_controllers = filter(lambda c: c in self.simulation.controller_names, component)
    # Is this a good size?
    return len(connected_controllers) > (len(self.simulation.controller_names) / 2)

  def RegisterController (self, controller):
    print "%s registered with Paxos Oracle" % (controller.name)
    self.registered_controllers[controller.name] = controller
  
  def InformOracleEvent (self, controller, event):
    # We have already accepted this, let us not do anything about it
    if event in self.already_accepted:
      return
    lengths = nx.shortest_path_length(self.simulation.graph, controller.name)
    ctrlr_lengths = 2 * max(map(lambda c: lengths.get(c, 0), self.simulation.controller_names))
    latency = sum(map(lambda c: controller.ctx.config.DataLatency, range(ctrlr_lengths)))
    prop_count = self.proposal_count
    self.proposal_count += 1
    controller.ctx.schedule_task(latency, \
                    lambda: self.ProposeAndAccept(controller, prop_count, event))

  def InformOracleEventNoCompute (self, controller, event):
    if event in self.already_proposed:
      self.proposers[event].add(controller.name)
    else:
      self.already_proposed.add(event)
      self.proposed.append(event)
      self.proposers[event] = set([controller.name])
      prop_count = self.proposal_count
      self.proposal_count += 1
      self.prop_count[event] = prop_count
      self.already_accepted.add(event)

  def ProposeAndAccept (self, controller, prop_count, event):
    if event in self.already_accepted:
      return
    # Someone already proposed this, just record that a new proposer has shown up
    elif event in self.already_proposed:
      self.proposers[event].add(controller.name)
    else:
      self.already_proposed.add(event)
      self.proposed.append(event)
      self.proposers[event] = set([controller.name])
      self.prop_count[event] = prop_count
    self.Accept()

  def Accept (self):
    # Now we know what to accept, figure out who can instantly
    # be informed
    components = nx.connected_components(self.simulation.graph)
    controllers = map(lambda component: \
                                  filter(lambda c: c in self.simulation.controller_names, component), \
                                components)
    controller_group_len = zip(map(lambda c: len(c), controllers), controllers)
    # Only the largest group can be the majority
    big_group = max(controller_group_len)[1]

    things_to_accept = []
    for proposed in self.proposed:
      for proposer in self.proposers[proposed]:
        if self.CheckConnectivity(proposer):
          things_to_accept.append(proposed)
          break
    if len(big_group) <= (len(self.simulation.controller_names) / 2):
      print "paxos not_available"
      assert(things_to_accept == [])
      return
    else:
      print "paxos available"
    for accept in things_to_accept:
      self.proposed.remove(accept)
      self.already_accepted.add(accept)
      self.already_proposed.remove(accept)
      self.accepted[self.prop_count[accept]] = accept
    for controller in big_group:
      if controller in self.registered_controllers:
        self.registered_controllers[controller].NotifyOracleDecision(self.accepted)
