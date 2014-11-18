from env import *
import networkx as nx
from controllers import *
    
def Main():
  ctx = Context()

  ControllerClass = PaxosController
  SwitchClass = LinkStateSwitch
  HostClass = Host
  
  ctrl0 = ControllerClass('c1', ctx, 10)
  ctrl1 = ControllerClass('c2', ctx, 11)
  ctrl2 = ControllerClass('c3', ctx, 12)
  ctrl3 = ControllerClass('c4', ctx, 13)
  ctrl4 = ControllerClass('c5', ctx, 14)

  switches = [SwitchClass('s%d'%(i), ctx) for i in xrange(1, 6)]

  host_a = HostClass('a', ctx, 1)
  host_b = HostClass('b', ctx, 2)
  host_c = HostClass('c', ctx, 3)
  host_d = HostClass('d', ctx, 4)
  host_e = HostClass('e', ctx, 5)

  hosts = [host_a, host_b, host_c, host_d, host_e]
  links = [Link(ctx, host_a, switches[0]), \
           Link(ctx, host_b, switches[1]), \
           Link(ctx, host_c, switches[2]), \
           Link(ctx, host_d, switches[3]), \
           Link(ctx, host_e, switches[4]), \
           Link(ctx, switches[0], switches[1]), \
           Link(ctx, switches[1], switches[2]), \
           Link(ctx, switches[0], switches[3]), \
           Link(ctx, switches[1], switches[3]), \
           Link(ctx, switches[2], switches[4]), \
           Link(ctx, switches[3], switches[4]), \
           Link(ctx, ctrl1, switches[1]), \
           Link(ctx, ctrl2, switches[2]), \
           Link(ctx, ctrl3, switches[3]), \
  ]

  linkFail =  Link(ctx, ctrl4, switches[4])
  links.append(linkFail)
  ctrl0.is_leader = True
  linkLowCtrl = Link(ctx, ctrl0, switches[0])

  for link in links:
    ctx.schedule_task(0, link.SetUp)
  ctx.schedule_task(100, linkLowCtrl.SetUp)

  print "Starting"
  ctx.schedule_task(5000, lambda: PaxosController.assert_rules([ctrl0, ctrl1, ctrl2, ctrl3, ctrl4]))

  ctx.schedule_task(5000, links[6].SetDown)
  ctx.schedule_task(5000, linkFail.SetDown)
  ctx.schedule_task(5000, links[5].SetDown)

  ctx.schedule_task(40000, lambda: PaxosController.assert_rules([ctrl0, ctrl1, ctrl2, ctrl3, ctrl4]))

  p = SourceDestinationPacket(1, 3)
  ctx.schedule_task(40000, lambda: host_a.Send(p))
  p2 = SourceDestinationPacket(1, 2)
  ctx.schedule_task(40000, lambda: host_a.Send(p2))

  p3 = SourceDestinationPacket(0, 4)
  ctx.schedule_task(40000, lambda: host_a.Send(p3))

  ctx.final_time = 50000
  ctx.run()
if __name__ == "__main__":
  Main()
