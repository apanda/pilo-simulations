import numpy.random
import yaml
import sys
def Main(simulation_setup, avg_time_events, set_all_links_up, total_events, stabilization_time, time_to_last_event):
  f = open(simulation_setup)
  x = f.read()
  setup = yaml.load(x)
  nhosts = len(filter(lambda h: h.startswith('h'), setup.keys()))
  links_up = set()
  links_down = set(setup['links'])
  if set_all_links_up:
    for link in setup['links']:
      print "0 %s up"%(link)
      links_up.add(link)
      links_down.remove(link)
  ctime = stabilization_time
  for ev in xrange(total_events):
    ctime = ctime + (avg_time_events * numpy.random.ranf())
    event = numpy.random.randint(3)
    if event == 0 and len(links_down) == 0:
      event = 1
    if event == 0:
      # Raise link from the dead
      link = numpy.random.choice(list(links_down))
      links_down.remove(link)
      links_up.add(link)
      print "%f %s up"%(ctime, link)
    elif event == 1:
      # Disconnect link
      link = numpy.random.choice(list(links_up))
      links_up.remove(link)
      links_down.add(link)
      print "%f %s down"%(ctime, link)
    else:
      # Send a message
      host = numpy.random.randint(nhosts) + 1
      dest = numpy.random.randint(nhosts) + 1
      hstr = "h%d"%(host)
      print "%f %s send %d %d"%(ctime, hstr, host, dest)
  print "%f end"%(ctime + time_to_last_event)

if __name__ == "__main__": 
  if len(sys.argv) < 7:
    print >>sys.stderr, """
      Usage:
      %s setup avg_delay set_all_links_up total_events stabilization_time time_to_last_event
         setup: YAML file
         avg_delay: Average delay between events
         set_all_links_up: Set all links up initially
         total_events: How many events to generate
         stabilization_time: How long to wait before doing interesting things
         time_to_last_event: How long to wait after last event
    """%(sys.argv[0])
    sys.exit(1)
  Main(sys.argv[1], \
       float(sys.argv[2]), \
       bool(sys.argv[3]), \
       int(sys.argv[4]), \
       float(sys.argv[5]), \
       float(sys.argv[6]))
