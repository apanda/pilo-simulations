import sys
import re
import numpy as np
if len(sys.argv) != 2:
  print "Usage: %s file"%(sys.argv[0])
  sys.exit(1)
f = open(sys.argv[1])
mean = None
latency = []
print "perturb min p5 p50 p95 max mean var"
for l in f:
  p = l.strip().split()
  #if p[0] == "mean_perturb" or re.match("^\d+?\.\d+?$", p[0]):
    #print l.strip()
  if p[0] == "mean_perturb":
    if mean:
       latency_min = min(latency)
       latency_max = max(latency)
       latency_5p = np.percentile(latency, 5)
       latency_95p = np.percentile(latency, 95)
       latency_med = np.percentile(latency, 50)
       latency_mean = np.mean(latency)
       latency_var = np.var(latency)
       print "%f %f %f %f %f %f %f %f"%(mean, \
                                     latency_min,\
                                     latency_5p,\
                                     latency_med,\
                                     latency_95p,\
                                     latency_max,\
                                     latency_mean,\
                                     latency_var)
    mean = float(p[1])
    latency = []
  elif re.match("^\d+?\.\d+?$", p[0]):
    clatency = eval(l.strip.split(' ', 5))
    if len(clatency) > 0:
       latency.extend(float(p[3]))
    
if mean and len(reachability) > 0:
   latency_min = min(reachability)
   latency_max = max(reachability)
   latency_5p = np.percentile(reachability, 5)
   latency_95p = np.percentile(reachability, 95)
   latency_med = np.percentile(reachability, 50)
   latency_mean = np.mean(reachability)
   latency_var = np.var(reachability)
   print "%f %f %f %f %f %f %f %f"%(mean, \
                                 latency_min,\
                                 latency_5p,\
                                 latency_med,\
                                 latency_95p,\
                                 latency_max,\
                                 latency_mean,\
                                 latency_var)
