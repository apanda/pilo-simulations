from env import *
import networkx as nx
class SpControl (Controller):
  def __init__ (self, ctx):
    super(SpControl, self).__init__('c0', ctx, 10)
    self.graph = nx.Graph()
    self.hosts = []
  def PacketIn(self, switch, source, packet):
    print "%s Don't know path, dropping packet from %d to %d"%\
            (switch.name, packet.source, packet.destination)
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
            self.UpdateRules(a, [(p.pack(), link)])
  def NotifySwitchUp (self, switch):
    #print "%f Heard about switch %s"%(self.ctx.now, switch.name)
    # Not sure this is necessary?
    self.graph.add_node(switch.name, switch = switch)
    if isinstance(switch, Host):
      self.hosts.append(switch)
    self.ComputeAndUpdatePaths()
    #self.graph[switch.name]['obj'] = switch
  def NotifyLinkUp (self, switch, link):
    #print "%f Heard about link %s"%(self.ctx.now, link)
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    self.ComputeAndUpdatePaths()
  def NotifyLinkDown (self, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    self.graph.remove_edge(link.a.name, link.b.name)
    self.ComputeAndUpdatePaths()

def Main():
  ctx = Context()
  ctrl = SpControl(ctx)
  switches = [Switch('s%d'%(i), ctx) for i in xrange(1, 4)]
  for switch in switches:
    ctx.schedule_task(0, switch.anounceToController)
  host_a = Host('a', ctx, 1)
  host_b = Host('b', ctx, 2)
  host_c = Host('c', ctx, 3)
  hosts = [host_a, host_b, host_c]
  links = [Link(ctx, host_a, switches[0]), \
           Link(ctx, host_b, switches[1]), \
           Link(ctx, host_c, switches[2]), \
           Link(ctx, switches[0], switches[1]), \
           Link(ctx, ctrl, switches[1]), \
           Link(ctx, switches[1], switches[2]), \
           Link(ctx, switches[0], switches[2])]
  for link in links:
    ctx.schedule_task(1, link.SetUp)
  for host in hosts:
    ctx.schedule_task(100, host.anounceToController)
  print "Starting"
  p = SourceDestinationPacket(1, 3)
  ctx.schedule_task(800, lambda: host_a.Send(p))
  p2 = SourceDestinationPacket(2, 3)
  ctx.schedule_task(800, lambda: host_a.Send(p2))
  p3 = FloodPacket("Hello")
  ctx.schedule_task(800, lambda: host_a.Send(p3))
  ctx.final_time = 2000
  ctx.run()
if __name__ == "__main__":
  Main()
