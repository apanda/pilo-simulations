from env import *
import networkx as nx

class CoordinatingControl (LS2PCController):
  def __init__ (self, name, ctx, address):
    super(CoordinatingControl, self).__init__(name, ctx, address)
    self.hosts = set()
    self.controllers = set([self.name])
    self.switches = set()
    self.graph.add_node(self.name)

  def PacketIn(self, pkt, src, switch, source, packet):
    print "(%s) %s Don't know path, dropping packet from %d to %d"%\
            (self.name, switch.name, packet.source, packet.destination)

  def ShouldBeCurrentLeader (self, switch):
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller
    return None


  def NewlyAppointedLeader(self, src):
     self.ComputeAndUpdatePaths() # Update switch as necessary
  def NewlyRemovedLeader (self, src):
    self.ComputeAndUpdatePaths()

  def currentLeader(self, a):
    if a in self.currently_leader_for:
      return self.name
    return ""

  def ComputeAndUpdatePaths (self):
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    #print "%f Shortest paths are "%(self.ctx.now)
    #print sp
    #print "%f hosts are %s"%(self.ctx.now ,self.hosts)
    for host in self.hosts:
      for h2 in self.hosts:
        if h2 == host:
          continue
        if h2.name in sp[host.name]:
          p = SourceDestinationPacket(host.address, h2.address)
          path = zip(sp[host.name][h2.name], \
                    sp[host.name][h2.name][1:])
          for (a, b) in path[1:]:
            #if 'switch' not in self.graph.node[a]:
              #continue      
            #ao = self.graph.node[a]['switch']
            link = self.graph[a][b]['link']
            if a in self.currently_leader_for:
              #print "%f %s leader for %s controllers are %s"%(self.ctx.now, self.name, a, self.controllers)
              self.UpdateRules(a, [(p.pack(), link)])
    self.updateSwitchLeadership()

  def updateSwitchLeadership (self):
    for switch in self.switches:
      if self.ShouldBeCurrentLeader(switch) == self.name and \
              switch not in self.currently_leader_for:
        # Request that we become the leader. In many cases this 
        # will fail
        self.SetSwitchLeadership(switch, self.name)

  
  def maintainSets(self, switch):
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    elif isinstance(switch, HostTrait):
      self.hosts.add(switch)
    else:
      self.switches.add(switch.name)

  def NotifySwitchUp (self, pkt, src, switch):
    #print "%f Heard about switch %s"%(self.ctx.now, switch.name)
    # Not sure this is necessary?
    self.graph.add_node(switch.name, switch = switch)
    self.maintainSets(switch)
    self.ComputeAndUpdatePaths()
    #self.graph[switch.name]['obj'] = switch

  def NotifyLinkUp (self, pkt, src, switch, link):
    #print "%f Heard about link %s"%(self.ctx.now, link)
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    assert(switch.name in self.graph)
    self.maintainSets(switch)
    self.ComputeAndUpdatePaths()
    if link.a.name == self.name or link.b.name == self.name:
      # Something changed for us, find out (essentially we know for sure
      # we need to query information). Actually we should probably query all
      # the time when a link comes up (stuff has changed)
      self.GetSwitchInformation()

  def NotifyLinkDown (self, pkt, src, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    if self.graph.has_edge(link.a.name, link.b.name):
      self.graph.remove_edge(link.a.name, link.b.name)
    elif switch.name not in self.graph:
      self.graph.add_node(switch.name)
    assert(switch.name in self.graph)
    self.maintainSets(switch)
    self.ComputeAndUpdatePaths()

  def NotifySwitchInformation (self, pkt, src, switch, links):
    self.maintainSets(switch)
    neighbors = map(lambda l: l.a.name if l.b.name == switch.name else l.b.name, links)
    neighbor_to_link = dict(zip(neighbors, links))
    self.graph.add_node(switch.name)
    g_neighbors = self.graph.neighbors(switch.name)
    gn_set = set(g_neighbors)
    n_set = set(neighbors)
    for neighbor in neighbors:
      if neighbor not in gn_set:
        self.graph.add_edge(switch.name, neighbor, link=neighbor_to_link[neighbor])
    for neighbor in g_neighbors:
      if neighbor not in n_set:
        self.graph.remove_edge(switch.name, neighbor)
    assert(switch.name in self.graph)
    self.ComputeAndUpdatePaths()
