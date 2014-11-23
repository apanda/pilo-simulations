import sys
from sim import Simulation
def Main (args):
  if len(args) < 2 or len(args) > 4:
    print >>sys.stderr, "Usage: simulation.py setup trace [show_converge]"
  else:
    sim = Simulation()
    print "Simulation is %s"%sim
    topo = args[0]
    trace = args[1]
    show_converge = bool(args[2]) if len(args) > 2 else False
    sim.Setup(topo, trace)
    sim.Run()
    sim.Report(show_converge)

if __name__ == "__main__":
  Main(sys.argv[1:])
