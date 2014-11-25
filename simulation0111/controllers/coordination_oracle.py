from env import Singleton
from sim import Simulation
import networkx as nx

class CoordinationOracle (object):
  """Perfect coordination"""
  __metaclass__ = Singleton
  def __init__ (self):
    self.simulation = Simulation()
    self.proposed = []
    #self.accepted = {}
    self.proposal_count = 0
    self.registered_controllers = {}
    self.already_proposed = set()
    #self.already_accepted = set()
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
  
  def RegisterController (self, controller):
    print "%s registered with Coordination Oracle" % (controller.name)
    self.registered_controllers[controller.name] = controller
  
  def InformOracleEvent (self, controller, event):
    lengths = nx.shortest_path_length(self.simulation.graph, controller.name)
    ctrlr_lengths = 2 * max(map(lambda c: lengths.get(c, 0), self.simulation.controller_names))
    latency = sum(map(lambda c: controller.ctx.config.DataLatency, range(ctrlr_lengths)))
    prop_count = self.proposal_count
    self.proposal_count += 1
    controller.ctx.schedule_task(latency, \
                    lambda: self.ProposeAndAccept(controller, prop_count, event))

  def ProposeAndAccept (self, controller, prop_count, event):
    # Someone already proposed this, just record that a new proposer has shown up
    if event in self.already_proposed:
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
    components = map(lambda component: \
                       filter(lambda c: c in self.simulation.controller_names, component), \
                                           nx.connected_components(self.simulation.graph))
    components = zip(range(len(components)), components)
    to_accept = [[] for i in components]
    for proposed in self.proposed:
      already_added = set()
      for proposer in self.proposers[proposed]:
        group = filter(lambda (idx, component): proposer in component, components)[0]
        if group[0] not in already_added:
          to_accept[group[0]].append(proposed)
    for (idx, controllers) in components:
      for controller in controllers:
        if controller in self.registered_controllers:
          print "Notifying %s of events"%(controller)
          self.registered_controllers[controller].NotifyOracleDecision(to_accept[idx])
