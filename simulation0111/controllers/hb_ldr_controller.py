from env import *
import networkx as nx
"""Switches recongnize leaders in this case"""
class HBControl (HBController):
  def __init__ (self, name, ctx, address, epoch, send_rate):
    super(HBControl, self).__init__(name, ctx, address, epoch, send_rate)
    self.graph = nx.Graph()
    self.hosts = set()
    self.controllers = set([self.name])
    self.graph.add_node(self.name)

  def PacketIn(self, src, switch, source, packet):
    pass

  def currentLeader (self, switch):
    connectivity_measure = sorted(map(lambda c: (-1 * len(self.connectivityMatrix.get(c, [])), c), self.controllers))
    for (m, c) in connectivity_measure:
      if nx.has_path(self.graph, c, switch):
        return c

  def ComputeAndUpdatePaths (self):
    #print "%f %s updating paths, hosts are %s"%(self.ctx.now, self.name, self.hosts)
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    #print "%f Shortest paths are "%(self.ctx.now)
    #print sp
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

  def NotifySwitchUp (self, src, switch):
    #print "%f Heard about switch %s"%(self.ctx.now, switch.name)
    # Not sure this is necessary?
    self.graph.add_node(switch.name, switch = switch)
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()
    #self.graph[switch.name]['obj'] = switch

  def NotifyLinkUp (self, src, switch, link):
    #print "%f Heard about link %s"%(self.ctx.now, link)
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    assert(switch.name in self.graph)
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()

  def NotifyLinkDown (self, src, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    if self.graph.has_edge(link.a.name, link.b.name):
      self.graph.remove_edge(link.a.name, link.b.name)
    assert(switch.name in self.graph)
    if isinstance(switch, HostTrait):
      self.hosts.append(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()

  def NotifySwitchInformation (self, src, switch, links):
    assert (False)

  def processHeartbeat(self, hbpacket):
    super(HBControl, self).processHeartbeat(hbpacket)
    if isinstance(hbpacket.sobj, HostTrait):
      self.hosts.add(hbpacket.sobj)
    if isinstance(hbpacket.sobj, HBController):
      self.controllers.add(hbpacket.sobj.name)
    neighbors = map(lambda l: l.a.name if l.b.name == hbpacket.src else l.b.name, hbpacket.direct_links)
    neighbor_to_link = dict(zip(neighbors, hbpacket.direct_links))
    self.graph.add_node(hbpacket.src)
    g_neighbors = self.graph.neighbors(hbpacket.src)
    gn_set = set(g_neighbors)
    n_set = set(neighbors)
    for neighbor in neighbors:
      if neighbor not in gn_set:
        self.graph.add_edge(hbpacket.src, neighbor, link=neighbor_to_link[neighbor])
    for neighbor in g_neighbors:
      if neighbor not in n_set:
        self.graph.remove_edge(hbpacket.src, neighbor)
    assert(hbpacket.src in self.graph)
    self.ComputeAndUpdatePaths()
  
  def UpdatedConnectivity(self):
    pass
