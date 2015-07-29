import sys
from sim import Simulation
import numpy as np
import numpy.random as random
from itertools import permutations
from env import Singleton 
from collections import defaultdict
import yaml
import argparse
"""Generate a trace with links fail and are recovered at a time independent of failure"""
def TransformTrace (links, fail_links, mttf, mttr, stable, end_time, bootstrap):
  new_trace = []
  ctime = 0.0
  #for link in links:
    #new_trace.append("%f %s up"%(ctime, link))
  ctime += stable
  up_links = set(links)
  down_links = set()
  set_up_at = defaultdict(list)

  # We don't want to do anything, this is just a placeholder
  # Otherwise end instantly
  new_trace.append("%f end"%end_time)
  return (end_time, new_trace)

def Main (argv):
  show_converge = True
  parser = argparse.ArgumentParser(description="Run without bootup")
  parser.add_argument('--setup', nargs=1, help="Setup", dest="setup",)
  parser.add_argument('--stable', nargs=1, help="Stable time", dest="stable")
  parser.add_argument('--mttr', nargs=1, help="MTTR", dest="mttr")
  parser.add_argument('--end', nargs=1, help="End time", dest="end")
  parser.add_argument('--perturb_begin', nargs=1, dest="bmp")
  parser.add_argument('--perturb_end', nargs=1, dest="emp")
  parser.add_argument('--perturb_step', nargs=1, dest="smp")
  parser.add_argument('--sample', nargs=1, dest="sample")
  parser.add_argument('--seed', nargs=1, dest="seed")
  parser.add_argument('--bootstrap', nargs=1, dest='boot', help='Should bootstrap (true) or not')
  parser.add_argument('--config', nargs=1, dest='cfg', help='Config file')
  parser.add_argument('-?', action='help')
  args = parser.parse_args(argv[1:])
  topo = open(args.setup[0]).read()
  stable = float(args.stable[0])
  mean_recovery = float(args.mttr[0])
  end_time = float(args.end[0])
  begin = float(args.bmp[0])
  end = float(args.emp[0])
  step = float(args.smp[0])
  sampling_rate = float(args.sample[0])
  seed = int(args.seed[0])
  bootstrap = (args.boot[0].lower() == "true")
  config_file = str(args.cfg[0])
  print "Setting %s %f %f %f %f %f %f %f %d %s"%(argv[0], stable, mean_recovery, end_time, begin, end,\
                                              step, sampling_rate, seed, config_file)
  topo_yaml = yaml.load(topo)

  links = topo_yaml['links']

  # If no fail links then just use links
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
    (end_time, new_trace) = TransformTrace(links, fail_links, mean, mean_recovery, stable, end_time, bootstrap)
    print "done generating trace"
    print "TRACE TRACE TRACE"
    for t in new_trace:
      print t
    print "TRACE TRACE TRACE"
    links = sim.Setup(topo, new_trace, False, count_ctrl_packet=True, count_packets=1, no_bootstrap = True, config_file = config_file)
    max_link = max(links.items(), key=lambda (l, c): c)
    print "Max link is %s"%(str(max_link))
    zero_links = filter(lambda (l, c): c==0, links.items())
    print "Total links %d zero links %d Zero Links %s"%(len(links.items()), len(zero_links), zero_links)
    sim.scheduleLinkDown(2.0, str(max_link[0]))

    for time in np.arange(stable, end_time, sampling_rate):
      sim.scheduleCheck(time)
    sim.Run()
    sim.Report(show_converge)
    sim.Clear()

if __name__ == "__main__":
  Main(sys.argv)
