from env import *
import networkx as nx
class HBControl (HBController):
  def __init__ (self, name, ctx, addr, epoch, send_rate):
    super(HBControl, self).__init__(name, ctx, addr, epoch, send_rate)
    self.graph = nx.Graph()
    self.hosts = set()
    self.controllers = set([self.name])
    self.graph.add_node(self.name)

  def PacketIn(self, src, switch, source, packet):
    print "(%s) %s Don't know path, dropping packet from %d to %d"%\
            (self.name, switch.name, packet.source, packet.destination)

  def currentLeader (self, switch):
    connectivity_measure = sorted(map(lambda c: (len(self.connectivityMatrix.get(c, [])), c), self.controllers), \
                                  reverse = True)
    for (m, c) in connectivity_measure:
      if nx.has_path(self.graph, c, switch):
        return c

  def ComputeAndUpdatePaths (self):
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
            #print "%f %s For %s current leader is %s"%(self.ctx.now, self.name, a, self.currentLeader(a))
            if self.currentLeader(a) == self.name:
              self.UpdateRules(a, [(p.pack(), link)])

  def NotifySwitchUp (self, src, switch):
    #print "%f Heard about switch %s"%(self.ctx.now, switch.name)
    # Not sure this is necessary?
    self.graph.add_node(switch.name, switch = switch)
    if isinstance(switch, HBHost):
      self.hosts.add(switch)
    if isinstance(switch, Controller):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()
    #self.graph[switch.name]['obj'] = switch

  def NotifyLinkUp (self, src, switch, link):
    #print "%f Heard about link %s"%(self.ctx.now, link)
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    assert(switch.name in self.graph)
    if isinstance(switch, HBHost):
      self.hosts.add(switch)
    if isinstance(switch, Controller):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()

  def NotifyLinkDown (self, src, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    if self.graph.has_edge(link.a.name, link.b.name):
      self.graph.remove_edge(link.a.name, link.b.name)
    assert(switch.name in self.graph)
    if isinstance(switch, HBHost):
      self.hosts.append(switch)
    if isinstance(switch, Controller):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()

  def NotifySwitchInformation (self, src, switch, links):
    assert (False)

  def processHeartbeat(self, hbpacket):
    super(HBControl, self).processHeartbeat(hbpacket)
    if isinstance(hbpacket.sobj, HBHost):
      self.hosts.add(hbpacket.sobj)
    if isinstance(hbpacket.sobj, HBController):
      self.controllers.add(hbpacket.sobj.name)
    neighbors = map(lambda l: l.a.name if l.b.name == hbpacket.src else l.b.name, hbpacket.direct_links)
    neighbor_to_link = dict(zip(neighbors, hbpacket.direct_links))
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

def Main():
  ctx = Context()
  EPOCH = 5000
  SEND_RATE = 200
  ctrl0 = HBControl('c1', ctx, 10, EPOCH, SEND_RATE)
  ctrl1 = HBControl('c2', ctx, 11, EPOCH, SEND_RATE)
  switches = [HBSwitch('s%d'%(i), ctx, EPOCH, SEND_RATE)\
          for i in xrange(1, 4)]
  host_a = HBHost('a', ctx, 1, EPOCH, SEND_RATE)
  host_b = HBHost('b', ctx, 2, EPOCH, SEND_RATE)
  host_c = HBHost('c', ctx, 3, EPOCH, SEND_RATE)
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
  #ctx.schedule_task(1500, linkLowCtrl.SetDown)
  ctx.final_time = 8000
  ctx.run()
if __name__ == "__main__":
  Main()
