from env import *
import networkx as nx
class SpControl (Controller):
  def __init__ (self, ctx):
    super(SpControl, self).__init__(ctx)
    self.graph = nx.Graph()
  def NotifySwitchUp (self, switch):
    self.graph.add_node(switch.name, switch = switch)
    print "%d %s"%(self.ctx.now, switch.name)
    #self.graph[switch.name]['obj'] = switch
  def NotifyLinkUp (self, switch, link):
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    print self.ctx.now,
    print nx.shortest_paths.all_pairs_shortest_path(self.graph)
  def NotifyLinkDown (self, switch, link):
    self.graph.remove_edge(link.a.name, link.b.name)
    print self.ctx.now,
    print nx.shortest_paths.all_pairs_shortest_path(self.graph)

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
    ctx.schedule_task(0, switch.anounceToController)
  links = [Link(ctx, host_a, switches[0]), \
           Link(ctx, host_b, switches[1]), \
           Link(ctx, host_c, switches[2]), \
           Link(ctx, switches[0], switches[1]), \
           Link(ctx, switches[1], switches[2]), \
           Link(ctx, switches[0], switches[2])]
  for link in links:
    ctx.schedule_task(1, link.SetUp)
  print "Starting"
  ctx.run()
if __name__ == "__main__":
  Main()
