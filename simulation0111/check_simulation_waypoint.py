from env import *
import networkx as nx
from controllers import *
    
def Main():
  ctx = Context()

  ControllerClass = WpControlClass(CoordinatingControl)
  SwitchClass = WaypointSwitchClass(LS2PCSwitch)
  HostClass = WaypointHostClass(Host)
  
  ctrl0 = ControllerClass('c1', ctx, 10)
  ctrl1 = ControllerClass('c2', ctx, 11)

  switches = [SwitchClass('s%d'%(i), ctx) for i in xrange(1, 4)]

  host_a = HostClass('a', ctx, 1)
  host_b = HostClass('b', ctx, 2)
  host_c = HostClass('c', ctx, 3)
  hosts = [host_a, host_b, host_c]
  links = [Link(ctx, host_a, switches[0]), \
           Link(ctx, host_b, switches[1]), \
           Link(ctx, host_c, switches[2]), \
           Link(ctx, switches[0], switches[1]), \
           Link(ctx, ctrl1, switches[1]), \
           Link(ctx, switches[1], switches[2]), \
           Link(ctx, switches[0], switches[2])]

  waypoint_rules = {
    host_a: ("s3", None),
    host_c: (None, "s2")
  }

  for link in links:
    ctx.schedule_task(0, link.SetUp)

  linkLowCtrl = Link(ctx, ctrl0, switches[0])
  ctx.schedule_task(100, linkLowCtrl.SetUp)
  print "Starting"
  p = SourceDestinationPacket(1, 3)
  ctx.schedule_task(1000, lambda: host_a.Send(p))
  p2 = SourceDestinationPacket(1, 2)
  ctx.schedule_task(1000, lambda: host_a.Send(p2))
  p3 = FloodPacket("Hello")
  ctx.schedule_task(1000, lambda: host_a.Send(p3))

  ctx.schedule_task(1000, lambda: ctrl0.changeWaypointRules(waypoint_rules))
  p4 = MarkedSourceDestPacket(2, 3)
  ctx.schedule_task(5000, lambda: host_b.Send(p4))

  p5 = MarkedSourceDestPacket(1, 2)
  ctx.schedule_task(5500, lambda: host_c.Send(p5))

  ctx.final_time = 8000
  ctx.run()
if __name__ == "__main__":
  Main()
