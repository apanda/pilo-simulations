import sys
import re
import numpy as np
if len(sys.argv) != 2:
  print "Usage: %s file"%(sys.argv[0])
  sys.exit(1)
f = open(sys.argv[1])
mean = None
avail = 0
not_avail = 0
convergence = False
print "perturb avail not_avail"
for l in f:
  p = l.strip().split()
  #if p[0] == "mean_perturb" or re.match("^\d+?\.\d+?$", p[0]):
    #print l.strip()
  if p[0] == "mean_perturb":
    convergence = False
    if mean:
      print "%f %d %d %f"%(mean, \
                        avail, \
                        not_avail, \
                        100.0 * (float(avail) / float(avail + not_avail)))
       #components_min = min(components)
       #components_max = max(components)
       #components_5p = np.percentile(components, 5)
       #components_95p = np.percentile(components, 95)
       #components_med = np.percentile(components, 50)
       #components_mean = np.mean(components)
       #components_var = np.var(components)
    mean = float(p[1])
    components = []
    avail = 0
    not_avail = 0
  elif p[0] == "paxos":
    if p[1] == "available":
      avail += 1
    elif p[1] == "not_available": 
      not_avail += 1
    
if mean:
  print "%f %d %d %f"%(mean, \
                    avail, \
                    not_avail, \
                    100.0 * (float(avail) / float(avail + not_avail)))
