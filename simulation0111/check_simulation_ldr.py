from env import *
import networkx as nx
class SpControl (Controller):
  def __init__ (self, name, ctx, addr):
    super(SpControl, self).__init__(name, ctx, addr)
    self.graph = nx.Graph()
    self.hosts = set()
    self.controllers = set([self.name])
  def PacketIn(self, src, switch, source, packet):
    print "(%s) %s Don't know path, dropping packet from %d to %d"%\
            (self.name, switch.name, packet.source, packet.destination)

  def currentLeader (self, switch):
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller

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
            if self.currentLeader(a) == self.name:
              #print "%f %s leader for %s controllers are %s"%(self.ctx.now, self.name, a, self.controllers)
              self.UpdateRules(a, [(p.pack(), link)])

  def NotifySwitchUp (self, src, switch):
    #print "%f Heard about switch %s"%(self.ctx.now, switch.name)
    # Not sure this is necessary?
    self.graph.add_node(switch.name, switch = switch)
    if isinstance(switch, Host):
      self.hosts.add(switch)
    if isinstance(switch, Controller):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()
    #self.graph[switch.name]['obj'] = switch

  def NotifyLinkUp (self, src, switch, link):
    #print "%f Heard about link %s"%(self.ctx.now, link)
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    assert(switch.name in self.graph)
    if isinstance(switch, Host):
      self.hosts.add(switch)
    if isinstance(switch, Controller):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()
    if link.a.name == self.name or link.b.name == self.name:
      # Something changed for us, find out (essentially we know for sure
      # we need to query information). Actually we should probably query all
      # the time when a link comes up (stuff has changed)
      self.GetSwitchInformation()

  def NotifyLinkDown (self, src, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    if self.graph.has_edge(link.a.name, link.b.name):
      self.graph.remove_edge(link.a.name, link.b.name)
    assert(switch.name in self.graph)
    if isinstance(switch, Host):
      self.hosts.append(switch)
    if isinstance(switch, Controller):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()

  def NotifySwitchInformation (self, src, switch, links):
    if isinstance(switch, Host):
      self.hosts.add(switch)
    if isinstance(switch, Controller):
      self.controllers.add(switch.name)
    neighbors = map(lambda l: l.a.name if l.b.name == switch.name else l.b.name, links)
    neighbor_to_link = dict(zip(neighbors, links))
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

def Main():
  ctx = Context()
  ctrl0 = SpControl('c1', ctx, 10)
  ctrl1 = SpControl('c2', ctx, 11)
  switches = [LeaderComputingSwitch('s%d'%(i), ctx) for i in xrange(1, 4)]
  host_a = Host('a', ctx, 1)
  host_b = Host('b', ctx, 2)
  host_c = Host('c', ctx, 3)
  hosts = [host_a, host_b, host_c]
  links = [Link(ctx, host_a, switches[0]), \
           Link(ctx, host_b, switches[1]), \
           Link(ctx, host_c, switches[2]), \
           Link(ctx, switches[0], switches[1]), \
           Link(ctx, ctrl1, switches[1]), \
           Link(ctx, switches[1], switches[2]), \
           Link(ctx, switches[0], switches[2])]

  for link in links:
    ctx.schedule_task(0, link.SetUp)

  linkLowCtrl = Link(ctx, ctrl0, switches[0])
  ctx.schedule_task(100, linkLowCtrl.SetUp)
  print "Starting"
  p = SourceDestinationPacket(1, 3)
  ctx.schedule_task(800, lambda: host_a.Send(p))
  p2 = SourceDestinationPacket(2, 3)
  ctx.schedule_task(800, lambda: host_a.Send(p2))
  p3 = FloodPacket("Hello")
  ctx.schedule_task(800, lambda: host_a.Send(p3))
  ctx.schedule_task(1500, linkLowCtrl.SetDown)
  ctx.final_time = 8000
  ctx.run()
if __name__ == "__main__":
  Main()
