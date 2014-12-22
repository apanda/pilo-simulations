import sys
from sim import Simulation
import numpy as np
import numpy.random as random
from itertools import permutations
from env import Singleton 
from collections import defaultdict
import yaml
"""Generate a trace with links fail and are recovered at a time independent of failure"""
def TransformTrace (links, fail_links, mttf, mttr, stable, end_time):
  new_trace = []
  ctime = 0.0
  for link in links:
    new_trace.append("%f %s up"%(ctime, link))
  ctime += stable
  up_links = set(links)
  set_up_at = defaultdict(list)

  while ctime < end_time: 
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
    if ctime > end_time:
      break # Don't put things down if we are past time
    to_fail = None
    while to_fail not in up_links:
      to_fail = random.choice(list(fail_links))
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
  if ctime < end_time:
    ctime = end_time
  # Otherwise end instantly
  new_trace.append("%f end"%ctime)
  print "Done with trace"
  return (ctime, new_trace)

def Main (args):
  show_converge = True
  if len(args) != 9:
    print >>sys.stderr, "Usage: perturbation_constant.py setup stable_time mean_recovery end_time " + \
                                " begin_mean_perturb end_mean_perturn step_mean_perturb sampling_rate seed"
  else:
    topo = open(args[0]).read()
    stable = float(args[1])
    mean_recovery = float(args[2])
    end_time = float(args[3])
    begin = float(args[4])
    end = float(args[5])
    step = float(args[6])
    sampling_rate = float(args[7])
    seed = int(args[8])
    print "Setting %s %f %f %f %f %f %f %f %d"%(args[0], stable, mean_recovery, end_time, begin, end,\
            step, sampling_rate, seed)
    topo_yaml = yaml.load(topo)

    # If no fail links then just use links
    links = topo_yaml['links']

    if 'fail_links' in topo_yaml:
      fail_links = topo_yaml['fail_links']
    else:
      fail_links = links

    for mean in np.arange(begin, end, step):
      Singleton.clear()
      sim = Simulation()
      sim.check_always = False
      random.seed(seed)
      print "mean_perturb %f"%(mean)
      print "generating trace"
      (end_time, new_trace) = TransformTrace(links, fail_links, mean, mean_recovery, stable, end_time)
      print "done generating trace"
      print "TRACE TRACE TRACE"
      for t in new_trace:
        print t
      print "TRACE TRACE TRACE"
      sim.Setup(topo, new_trace, False)
      for time in np.arange(stable, end_time, sampling_rate):
        sim.scheduleCheck(time)
      # Measure latency less often
      for time in np.arange(stable, end_time, sampling_rate):
        for (ha, hb) in permutations(sim.hosts, 2):
          sim.scheduleSend(time, ha.name, ha.address, hb.address)
      sim.Run()
      sim.Report(show_converge)
      sim.Clear()

if __name__ == "__main__":
  Main(sys.argv[1:])
