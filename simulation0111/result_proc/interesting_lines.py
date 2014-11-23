import sys
import re
if len(sys.argv) != 2:
  print "Usage: %s file"%(sys.argv[0])
  sys.exit(1)
f = open(sys.argv[1])
for l in f:
  p = l.strip().split()
  if p[0] == "mean_perturb" or re.match("^\d+?\.\d+?$", p[0]):
    print l.strip()
