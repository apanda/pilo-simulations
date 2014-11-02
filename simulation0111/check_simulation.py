from env import *
import networkx as nx
class SpControl (Controller):
  def __init__ (self, ctx):
    super(SpControl, self).__init__(ctx)
    self.graph = nx.Graph()
    self.hosts = []
  def PacketIn(self, switch, source, packet):
    print "Don't know path, dropping packet from %d to %d"%\
            (packet.source, packet.destination)
  def NotifySwitchUp (self, switch):
    self.graph.add_node(switch.name, switch = switch)
    if isinstance(switch, Host):
      self.hosts.append(switch)
    #self.graph[switch.name]['obj'] = switch
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
            if 'switch' not in self.graph.node[a]:
              continue      
            ao = self.graph.node[a]['switch']
            link = self.graph[a][b]['link']
            self.UpdateRules(ao, [(p.pack(), link)])
  def NotifyLinkUp (self, switch, link):
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    self.ComputeAndUpdatePaths()
  def NotifyLinkDown (self, switch, link):
    self.graph.remove_edge(link.a.name, link.b.name)
    self.ComputeAndUpdatePaths()

def Main():
  ctx = Context()
  ctrl = SpControl(ctx)
  switches = [Switch('s%d'%(i), ctx, ctrl) for i in xrange(1, 4)]
  for switch in switches:
    ctx.schedule_task(0, switch.anounceToController)
  host_a = Host('a', ctx, ctrl, 1)
  host_b = Host('b', ctx, ctrl, 2)
  host_c = Host('c', ctx, ctrl, 3)
  hosts = [host_a, host_b, host_c]
  for host in hosts:
    ctx.schedule_task(0, host.anounceToController)
  links = [Link(ctx, host_a, switches[0]), \
           Link(ctx, host_b, switches[1]), \
           Link(ctx, host_c, switches[2]), \
           Link(ctx, switches[0], switches[1]), \
           Link(ctx, switches[1], switches[2]), \
           Link(ctx, switches[0], switches[2])]
  for link in links:
    ctx.schedule_task(1, link.SetUp)
  print "Starting"
  p = SourceDestinationPacket(1, 3)
  ctx.schedule_task(100, lambda: host_a.Send(p))
  p2 = SourceDestinationPacket(2, 3)
  ctx.schedule_task(100, lambda: host_a.Send(p2))
  p3 = FloodPacket("Hello")
  ctx.schedule_task(100, lambda: host_a.Send(p3))
  ctx.run()
if __name__ == "__main__":
  Main()
