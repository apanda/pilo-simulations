import networkx as nx
import numpy.random
import random
import yaml
import sys
import argparse
import matplotlib

config = [
   # Controller type, switch type, host type
   ("LSLeaderControl", "LinkStateSwitch", "Host", "controllers"),
   ("CoordinatingControl", "LS2PCSwitch", "Host", "controllers"),
   ("HBControl", "HBSwitch", "HBHost", "controllers"), 
   ("LSGossipControl", "LinkStateSwitch", "Host", "controllers"),
   ("LSTEControl", "LinkStateSwitch", "Host", "controllers"),
   ("LSPaxosOracleControl", "LinkStateSwitch", "Host", "controllers"),
   ("CoordinationOracleControl", "LinkStateSwitch", "Host", "controllers"),
   ("Controller2PC", "LinkStateSwitch", "Host", "controllers")
]

config_args =  \
{"HBControl": {"epoch": 5000, "send_rate": 1000, "addr": True},
 "HBSwitch": {"epoch": 5000, "send_rate": 1000},
 "HBHost": {"epoch": 5000, "send_rate": 1000},
 "LSLeaderControl": {"addr": True},
 "CoordinatingControl": {"addr": True},
 "LSGossipControl": {"addr": True},
 "LSGossipControl": {"addr": True},
 "LSPaxosOracleControl": {"addr": True},
 "CoordinationOracleControl": {"addr": True},
 "Controller2PC": {"addr": True}
}

def WriteGraph (hosts, controllers, switches, links, ct, st, ht, runfile):
  out = {}
  out['runfile'] = runfile
  out['links'] = links

  hcount = 0
  for host in hosts:
    out[host] = {'type': ht, 'args':{'address': hcount + 1}}
    hcount += 1

  for controller in controllers:
    out[controller] = {'type': ct} 
    if ct in config_args:
       out[controller]['args'] = {}
       for key in config_args[ct]:
         if key == 'addr':
           out[controller]['args']['address'] = hcount + 1
           hcount += 1
         else:
           out[controller]['args'][key] = config_args[ct][key]
  
  for switch in switches:
    out[switch] = {'type': st}
    if st in config_args:
       out[switch]['args'] = {}
       for key in config_args[st]:
          out[switch]['args'][key] = config_args[st][key]
  out['fail_links'] = filter(lambda l: 'h' not in l, links)
  return out

def process_file(topo, nhosts, ncontrollers):
  topo = open(topo)
  edges = []
  out = {}
  links = set()
  switches = set()
  for l in topo:
    l = l.strip()
    #l = l.replace('-', '')
    #l = l.replace(' ', '-')
    parts = l.split()
    l = 's%s-s%s'%(parts[0], parts[1])
    links.add(l)
    parts = l.split('-')
    switches.add(parts[0])
    switches.add(parts[1])
  switches = list(switches)
  host_prefix = "h"
  control_prefix = "c"
  hosts = set()
  for h in xrange(nhosts):
    host = "%s%d"%(host_prefix, h + 1)
    hosts.add(host)
    # Add random link
    switch = random.choice(switches)
    links.add("%s-%s"%(switch, host))
  controllers = set()
  for c in xrange(ncontrollers):
    controller = "%s%d"%(control_prefix, c+1)
    controllers.add(controller)
    switch = random.choice(switches)
    links.add("%s-%s"%(switch, controller))
  return (switches, list(hosts), list(controllers), list(links))


if __name__=="__main__":
  if len(sys.argv) < 5:
    print >>sys.stderr, "%s file nh nc pfx"%sys.argv[0]
    sys.exit(1)
  pfx = sys.argv[4]
  (all_switches, all_hosts, all_controllers, all_links) = \
      process_file(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
  idx = 0
  for (ct, st, ht, runfile) in config:
    out = WriteGraph(all_hosts, all_controllers, all_switches, all_links, ct, st, ht, runfile)
    f = open(pfx+str(idx)+".yaml", 'w')
    f.write(yaml.dump(out))
    f.close()
    idx += 1
