from env import *
from . import CoordinationOracle
import networkx as nx
class CoordinationOracleControl (LSController):
  def __init__ (self, name, ctx, address):
    super(CoordinationOracleControl, self).__init__(name, ctx, address)
    self.hosts = set()
    self.controllers = set([self.name])
    self.oracle = CoordinationOracle()
    self.oracle.RegisterController(self)

  def PacketIn(self, pkt, src, switch, source, packet):
    pass

  def currentLeader (self, switch):
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller

  def ComputeAndUpdatePaths (self):
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    for host in self.hosts:
      for h2 in self.hosts:
        if h2 == host:
          continue
        if h2.name in sp[host.name]:
          p = SourceDestinationPacket(host.address, h2.address)
          path = zip(sp[host.name][h2.name], \
                    sp[host.name][h2.name][1:])
          for (a, b) in path[1:]:
            link = self.graph[a][b]['link']
            if self.currentLeader(a) == self.name:
              self.UpdateRules(a, [(p.pack(), link)])
  
  def addLink (self, link):
    pass

  def removeLink (self, link):
    pass

  def UpdateMembers (self, switch):
    self.graph.add_node(switch.name)
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)

  def NotifySwitchUp (self, pkt, src, switch):
    self.oracle.InformOracleEvent(self, (pkt, src, switch, ControlPacket.NotifySwitchUp)) 

  def NotifyLinkUp (self, pkt, src, switch, link):
    self.oracle.InformOracleEvent(self, (pkt, src, switch, link, ControlPacket.NotifyLinkUp)) 

  def NotifyLinkDown (self, pkt, src, switch, link):
    self.oracle.InformOracleEvent(self, (pkt, src, switch, link, ControlPacket.NotifyLinkDown)) 

  def processSwitchUp (self, pkt, src, switch):
    self.UpdateMembers(switch)

  def processLinkUp (self, pkt, src, switch, link):
    self.UpdateMembers(switch)
    super(CoordinationOracleControl, self).addLink(link)
    #assert(switch.name in self.graph)

  def processLinkDown (self, pkt, src, switch, link): 
    self.UpdateMembers(switch)
    super(CoordinationOracleControl, self).removeLink(link)
    #assert(switch.name in self.graph)


  def NotifySwitchInformation (self, pkt, src, switch, links):
    assert(False)
  
  def NotifyOracleDecision (self, log):
    # Just process all to get us to a good state
    self.graph.clear()
    self.hosts.clear()
    self.controllers.clear()
    self.controllers.add(self.name)
    for entry in log:
      if entry[-1] == ControlPacket.NotifyLinkUp:
        self.processLinkUp(*entry[:-1])
      elif entry[-1] == ControlPacket.NotifyLinkDown:
        self.processLinkDown(*entry[:-1])
      elif entry[-1] == ControlPacket.NotifySwitchUp:
        self.processSwitchUp(*entry[:-1])
      else:
        print "Unknown entry entry"
    self.ComputeAndUpdatePaths()

