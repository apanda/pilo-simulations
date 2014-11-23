import sys
import re
import numpy as np
if len(sys.argv) != 2:
  print "Usage: %s file"%(sys.argv[0])
  sys.exit(1)
f = open(sys.argv[1])
mean = None
reachability = []
print "perturb min p5 p50 p95 max mean var"
for l in f:
  p = l.strip().split()
  #if p[0] == "mean_perturb" or re.match("^\d+?\.\d+?$", p[0]):
    #print l.strip()
  if p[0] == "mean_perturb":
    if mean:
       reachable_min = min(reachability)
       reachable_max = max(reachability)
       reachable_5p = np.percentile(reachability, 5)
       reachable_95p = np.percentile(reachability, 95)
       reachable_med = np.percentile(reachability, 50)
       reachable_mean = np.mean(reachability)
       reachable_var = np.var(reachability)
       print "%f %f %f %f %f %f %f"%(mean, \
                                     reachable_min,\
                                     reachable_5p,\
                                     reachable_med,\
                                     reachable_95p,\
                                     reachable_max,\
                                     reachable_mean,\
                                     reachable_var)
    mean = float(p[1])
    reachability = []
  elif re.match("^\d+?\.\d+?$", p[0]):
    reachability.append(float(p[3]))
