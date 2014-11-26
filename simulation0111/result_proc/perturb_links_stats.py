import sys
import re
import numpy as np
if len(sys.argv) != 2:
  print "Usage: %s file"%(sys.argv[0])
  sys.exit(1)
f = open(sys.argv[1])
mean = None
components = []
convergence = False
print "perturb min p5 p50 p95 max mean var"
for l in f:
  p = l.strip().split()
  #if p[0] == "mean_perturb" or re.match("^\d+?\.\d+?$", p[0]):
    #print l.strip()
  if p[0] == "mean_perturb":
    convergence = False
    if mean:
       components_min = min(components)
       components_max = max(components)
       components_5p = np.percentile(components, 5)
       components_95p = np.percentile(components, 95)
       components_med = np.percentile(components, 50)
       components_mean = np.mean(components)
       components_var = np.var(components)
       print "%f %f %f %f %f %f %f %f"%(mean, \
                                     components_min,\
                                     components_5p,\
                                     components_med,\
                                     components_95p,\
                                     components_max,\
                                     components_mean,\
                                     components_var)
    mean = float(p[1])
    components = []
  elif p[0] == "Convergence":
    convergence = True
  elif re.match("^\d+?\.\d+?$", p[0]) and convergence:
    components.append(float(p[-1]))
    
if mean and len(components) > 0:
   components_min = min(components)
   components_max = max(components)
   components_5p = np.percentile(components, 5)
   components_95p = np.percentile(components, 95)
   components_med = np.percentile(components, 50)
   components_mean = np.mean(components)
   components_var = np.var(components)
   print "%f %f %f %f %f %f %f %f"%(mean, \
                                 components_min,\
                                 components_5p,\
                                 components_med,\
                                 components_95p,\
                                 components_max,\
                                 components_mean,\
                                 components_var)
