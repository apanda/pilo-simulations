import sys
from sim import Simulation
import numpy as np
import numpy.random as random

def TransformTrace (trace, mean, stable):
  new_trace = []
  ctime = stable
  for t in trace:
    parts = t.strip().split() 
    if parts[-1] == 'up' or parts[-1] == 'down':
      if len(parts) == 3:
        new_trace.append(t.strip())
      else:
        ctime = ctime + mean * random.ranf()
        new_trace.append("%f %s"%(ctime, t.strip()))
    elif parts[-1] == 'end':
      ctime = ctime + float(parts[0])
      new_trace.append("%f end"%ctime)
  return new_trace

def Main (args):
  show_converge = True
  if len(args) != 7:
    print >>sys.stderr, "Usage: perturbation.py setup trace stable_time begin_mean_perturb end_mean_perturn step_mean_perturb seed"
  else:
    topo = open(args[0]).read()
    trace = open(args[1]).readlines()
    stable = float(args[2])
    begin = float(args[3])
    end = float(args[4])
    step = float(args[5])
    seed = float(args[6])
    sim = Simulation()
    random.seed(seed)
    for mean in np.arange(begin, end, step):
      print "mean_perturb %f"%(mean)
      new_trace = TransformTrace(trace, mean, stable)
      sim.Setup(topo, new_trace)
      sim.Run()
      sim.Report(show_converge)
      sim.Clear()

if __name__ == "__main__":
  Main(sys.argv[1:])
