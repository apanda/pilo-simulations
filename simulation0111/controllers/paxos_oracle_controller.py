from env import *
from . import PaxosOracle
import networkx as nx
from collections import defaultdict
class LSPaxosOracleControl (LSController):
  def __init__ (self, name, ctx, address):
    super(LSPaxosOracleControl, self).__init__(name, ctx, address)
    print "LS Paxos control %s"%name
    self.hosts = set()
    self.controllers = set([self.name])
    self.oracle = PaxosOracle()
    self.oracle.RegisterController(self)
    self.update_messages = {}
    self.link_version = {}
    self.switch_tables = defaultdict(lambda: defaultdict(lambda: None))
    self.reason = None

  def PacketIn(self, pkt, src, switch, source, packet):
    pass

  def currentLeader (self, switch):
    for c in sorted(list(self.controllers)):
      if c not in self.graph:
        self.graph.add_node(c)
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller


  def ComputeNoInstall (self):
    updates = defaultdict(lambda: [])
    current = 0
    for host in self.hosts:
      for h2 in self.hosts:
        if h2 == host:
          continue
        #print "Found path between %s and %s"%(host.name, h2.name)
        if host.name not in self.graph or h2.name not in self.graph:
          continue
        try:
          paths = list(nx.all_shortest_paths(self.graph, host.name, h2.name))
        except nx.exception.NetworkXNoPath:
          # No path
          continue
        # All of this is just some sort of ploy to get multipathing
        path = paths[current % len(paths)]
        current += 1
        p = SourceDestinationPacket(host.address, h2.address)
        path = zip(path, \
                   path[1:])
        for (a, b) in path[1:]:
          link = self.graph[a][b]['link']
          if self.switch_tables[a][p.pack()] != link:
            updates[a].append((p.pack(), link))
            self.switch_tables[a][p.pack()] = link
          #else:
              #print "%f %s skipping updating path from %s to %s since already"%(self.ctx.now, self.name, host, h2)
        #else:
          #print "%f No path found %s->%s %s"%(self.ctx.now, host, h2, self.graph.edges())
    return updates

  def ComputeAndUpdatePaths (self):
    #print "Computing paths now"
    #print "%f computing paths"%(self.ctx.now)
    updates = self.ComputeNoInstall()
    #if len(updates) == 0:
      #print "%f no updates"%self.ctx.now
    #else:
      #print "%f has updates"%self.ctx.now
    for a in updates.iterkeys():
      print "%f %s updating %s with len %d"%(self.ctx.now, self.name, a, len(updates[a]))
      print "Update to %s with len %d"%(a, len(updates[a]))
      if self.currentLeader(a) == self.name:
        self.update_messages[self.reason] = self.update_messages.get(self.reason, 0) + 1
        self.UpdateRules(a, updates[a])
  
  def UpdateMembers (self, switch):
    self.graph.add_node(switch.name)
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)

  def SwitchUpNoCompute(self , switch):
    self.processSwitchUp(None, switch)
    self.oracle.InformOracleEventNoCompute(self, (None, switch, ControlPacket.NotifySwitchUp))

  def NotifySwitchUp (self, pkt, src, switch):
    self.UpdateMembers(switch)
    self.oracle.InformOracleEvent(self, (src, switch, ControlPacket.NotifySwitchUp)) 

  def LinkUpNoCompute (self, version, switch, link):
    self.link_version[link] = version
    self.UpdateMembers(switch)
    self.addLink(link)
    self.oracle.InformOracleEventNoCompute(self, (version, None, switch, link, ControlPacket.NotifyLinkUp))

  def NotifyLinkUp (self, pkt, version, src, switch, link):
    self.UpdateMembers(switch)
    self.oracle.InformOracleEvent(self, (version, src, switch, link, ControlPacket.NotifyLinkUp)) 

  def NotifyLinkDown (self, pkt, version, src, switch, link):
    self.UpdateMembers(switch)
    self.oracle.InformOracleEvent(self, (version, src, switch, link, ControlPacket.NotifyLinkDown)) 

  def processSwitchUp (self, src, switch):
    self.UpdateMembers(switch)

  def processLinkUp (self, version, src, switch, link):
    if self.link_version.get(version, 0) > version:
      return
    self.link_version[link] = version
    self.UpdateMembers(switch)
    self.addLink(link)
    #assert(switch.name in self.graph)

  def processLinkDown (self, version, src, switch, link): 
    if self.link_version.get(version, 0) > version:
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
