import numpy.random
import yaml
import sys
import argparse
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
  parser = argparse.ArgumentParser(description="Run this script to generate a random trace")
  
  parser.add_argument("-f", metavar="file", help="Name of the setup YAML file")
  parser.add_argument("--delay", metavar="d", type=float, help="Average delay between events")
  parser.add_argument("--init", dest="init", action="store_true", default=False, help="Whether to set up all links initially")
  parser.add_argument("-e", metavar="num_events", type=int, help="Total number of events to generate")
  parser.add_argument("-t1", type=float, help="Stabilization time: how long to wait before generating the first event")
  parser.add_argument("-t2", type=float, help="Time to last event: how long to run the simulator after the last event is triggered")
  args = parser.parse_args()

  Main(args.f,
       args.delay,
       args.init,
       args.e,
       args.t1,
       args.t2)
