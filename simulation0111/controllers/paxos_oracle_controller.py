from env import *
from . import PaxosOracle
import networkx as nx
class LSPaxosOracleControl (LSController):
  def __init__ (self, name, ctx, address):
    super(LSPaxosOracleControl, self).__init__(name, ctx, address)
    self.hosts = set()
    self.controllers = set([self.name])
    self.oracle = PaxosOracle()
    self.oracle.RegisterController(self)
    self.update_messages = {}
    self.link_version = {}
    self.reason = None
    self.GetSwitchInformation()

  def PacketIn(self, pkt, src, switch, source, packet):
    pass

  def currentLeader (self, switch):
    for c in sorted(list(self.controllers)):
      if c not in self.graph:
        self.graph.add_node(c)
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
              self.update_messages[self.reason] = self.update_messages.get(self.reason, 0) + 1
              self.UpdateRules(a, [(p.pack(), link)])
  
  def UpdateMembers (self, switch):
    self.graph.add_node(switch.name)
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)

  def NotifySwitchUp (self, pkt, src, switch):
    self.UpdateMembers(switch)
    self.oracle.InformOracleEvent(self, (src, switch, ControlPacket.NotifySwitchUp)) 

  def NotifyLinkUp (self, pkt, version, src, switch, link):
    self.UpdateMembers(switch)
    self.oracle.InformOracleEvent(self, (version, src, switch, link, ControlPacket.NotifyLinkUp)) 

  def NotifyLinkDown (self, pkt, version, src, switch, link):
    self.UpdateMembers(switch)
    self.oracle.InformOracleEvent(self, (version, src, switch, link, ControlPacket.NotifyLinkDown)) 

  def processSwitchUp (self, src, switch):
    self.UpdateMembers(switch)

  def processLinkUp (self, version, src, switch, link):
    if self.link_version.get(version, 0) >= version:
      return
    self.link_version[link] = version
    self.UpdateMembers(switch)
    self.addLink(link)
    #assert(switch.name in self.graph)

  def processLinkDown (self, version, src, switch, link): 
    if self.link_version.get(version, 0) >= version:
      return
    self.link_version[link] = version
    self.UpdateMembers(switch)
    self.removeLink(link)
    #assert(switch.name in self.graph)


  def NotifySwitchInformation (self, pkt, src, switch, version_links):
    for (v, l) in version_links:
      if self.link_version.get(l, 0) < v:
        self.oracle.InformOracleEvent(self, (v, src, switch, l, ControlPacket.NotifyLinkUp))
  
  def NotifyOracleDecision (self, log):
    self.reason = "NotifyOracleDecision"
    # Just process all to get us to a good state
    self.graph.clear()
    self.hosts.clear()
    self.controllers.clear()
    self.link_version = {}
    self.controllers.add(self.name)
    for prop in sorted(log.keys()):
      entry = log[prop]
      if entry[-1] == ControlPacket.NotifyLinkUp:
        self.processLinkUp(*entry[:-1])
      elif entry[-1] == ControlPacket.NotifyLinkDown:
        self.processLinkDown(*entry[:-1])
      elif entry[-1] == ControlPacket.NotifySwitchUp:
        self.processSwitchUp(*entry[:-1])
      else:
        print "Unknown entry entry"
    self.ComputeAndUpdatePaths()
    self.reason = None
