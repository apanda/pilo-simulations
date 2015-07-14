import matplotlib.pyplot as plt
import sys
import re
#from mpltools import style
#from mpltools import layout
import numpy

flist = sys.argv[1:]

fig, ax = plt.subplots(ncols=1, nrows=1)
for fname in flist:
    f = open(fname, 'r')
    convergence = False
    x = []
    y = []
    for line in f:
        if line.startswith("Convergence"):
            convergence = True
        if convergence:
            l = line.split(' ')
            time = float(l[0])
            converge = float(l[3])
            x.append(time)
            y.append(converge)

    ax.plot(x, y, label=fname, linewidth=3)
        
    f.close()

plt.savefig("graph.pdf")
