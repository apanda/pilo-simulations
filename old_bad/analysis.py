import numpy as np
from itertools import izip
from math import ceil
def epochs_away (latency_mean, epochs, epoch_time):
  received_epochs = []
  curr_time = 0
  for epoch in xrange(epochs):
    curr_time += epoch_time
    received_epochs.append(curr_time + np.random.poisson(latency_mean))
    received_epochs.append(curr_time + latency_mean)
  diffs = [(b - a) for (a, b) in izip(received_epochs, received_epochs[1:])]
  return diffs
latencies = [23,\
             34,\
             29,\
             26,\
             19,\
             17,\
             37,\
             22,\
             20,\
             31,\
             25,\
             52,\
             31,\
             8 ,\
             12,\
             24,\
             12,\
             22,\
             38,\
             24,\
             46,\
             59,\
             20,\
             73,\
             21]

iters = 1
#print "lat epoch mean min median max stdev %over"
for it in xrange(iters):
  for latency in latencies:
    for ep_time in np.arange(0.5, 5.0, 0.5):
      epoch_time = ep_time * latency
      diffs = epochs_away(latency, 100000, epoch_time)
      #print "%f %f %f %f %f %f %f %f"%(latency, \
                                    #ep_time * latency, \
                                    #np.mean(diffs), \
                                    #np.amin(diffs), \
                                    #np.median(diffs), \
                                    #np.amax(diffs), \
                                    #np.std(diffs), \
                                    #float(len(filter(lambda x: x > (ep_time * latency), diffs))) / float(len(diffs)))
      normed_epochs = map(lambda f: ceil(f/epoch_time), diffs)
      (hist, bin_edges) = np.histogram(normed_epochs, bins=sorted(list(set(normed_epochs))), density=True)
      bins = izip(bin_edges, bin_edges[1:])
      hist_string = ' '.join(map(lambda (s, e), value: "%f-%f: %f"%(s, e, value), bins, hist))
      print "%f %f %s"%(latency, epoch_time, hist_string)
      #print "%f %f %s"%(latency, epoch_time, ' '.join(map(str, )))
