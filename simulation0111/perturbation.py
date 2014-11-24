import sys
from sim import Simulation
import numpy as np
import numpy.random as random
from itertools import permutations
from env import Singleton 

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
  return (ctime, new_trace)

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
    seed = int(args[6])
    print "Setting %s %s %f %f %f %f %d"%(args[0], args[1], stable, begin, end, step, seed)
    for mean in np.arange(begin, end, step):
      Singleton.clear()
      sim = Simulation()
      sim.check_always = False
      random.seed(seed)
      print "mean_perturb %f"%(mean)
      (end_time, new_trace) = TransformTrace(trace, mean, stable)
      sim.Setup(topo, new_trace, True)
      for time in np.arange(stable, end_time, 0.5 * mean):
        sim.scheduleCheck(time)
      # Measure latency less often
      for time in np.arange(stable, end_time, mean):
        for (ha, hb) in permutations(sim.hosts, 2):
          sim.scheduleSend(time, ha.name, ha.address, hb.address)
      sim.Run()
      sim.Report(show_converge)
      sim.Clear()

if __name__ == "__main__":
  Main(sys.argv[1:])
