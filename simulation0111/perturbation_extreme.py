import sys
from sim import Simulation
import numpy as np
import numpy.random as random
from itertools import permutations
from env import Singleton 
from collections import defaultdict
import yaml
"""Generate a trace with links fail and are recovered at a time independent of failure"""
def TransformTrace (links, nfailures, mttf, mttr, stable, wait):
  new_trace = []
  ctime = 0.0
  for link in links:
    new_trace.append("%f %s up"%(ctime, link))
  ctime += stable
  up_links = set(links)
  set_up_at = defaultdict(list)
  for fail in xrange(nfailures):
    ctime = ctime + mttf * random.ranf()
    set_up = list()
    for t in sorted(set_up_at.keys()):
      if t < ctime:
        for l in set_up_at[t]:
          new_trace.append("%f %s up"%(t, l))
          set_up.append(l)
        del(set_up_at[t])
    if len(up_links) == 0:
      # Nothing to fail
      continue
    to_fail = random.choice(list(up_links))
    up_links.remove(to_fail)
    new_trace.append("%f %s down"%(ctime, to_fail))
    recovery_time = random.exponential(mttr)
    assert(recovery_time) > 0
    set_up_at[ctime + recovery_time].append(to_fail)
    for l in set_up:
      up_links.add(l)
  for t in sorted(set_up_at.keys()):
    for l in set_up_at[t]:
      new_trace.append("%f %s up"%(t, l))
      up_links.add(l)
    ctime = t
  ctime += wait
  new_trace.append("%f end"%ctime)
  return (ctime, new_trace)

def Main (args):
  show_converge = True
  if len(args) != 9:
    print >>sys.stderr, "Usage: perturbation_extreme.py setup stable_time links_to_fail mean_recovery wait_at_end begin_mean_perturb end_mean_perturn step_mean_perturb seed"
  else:
    topo = open(args[0]).read()
    stable = float(args[1])
    links_to_fail = int(args[2])
    mean_recovery = float(args[3])
    wait = float(args[4])
    begin = float(args[5])
    end = float(args[6])
    step = float(args[7])
    seed = int(args[8])
    print "Setting %s %f %d %f %f %f %f %d"%(args[0], stable, links_to_fail, mean_recovery, begin, end, step, seed)
    links = yaml.load(topo)['links']

    for mean in np.arange(begin, end, step):
      Singleton.clear()
      sim = Simulation()
      sim.check_always = False
      random.seed(seed)
      print "mean_perturb %f"%(mean)
      print "generating trace"
      (end_time, new_trace) = TransformTrace(links, links_to_fail, mean, mean_recovery, stable, wait)
      print "done generating trace"
      print "TRACE TRACE TRACE"
      for t in new_trace:
        print t
      print "TRACE TRACE TRACE"
      sim.Setup(topo, new_trace, True)
      for time in np.arange(stable, end_time, 2 * mean):
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