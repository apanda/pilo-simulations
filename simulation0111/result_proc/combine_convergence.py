import sys
if len(sys.argv) < 2:
  print "Usage %s file"%(sys.argv[0])
  sys.exit(1)
f = open(sys.argv[1])
prevl = None
previous = None
for l in f:
  p = l.strip().split()[-1]
  if p != previous:
    if prevl:
      print prevl
    print l.strip()
    previous = p
  prevl = l.strip()
print prevl
