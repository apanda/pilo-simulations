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
 "LSPaxosOracleControl": {"addr": True},
 "CoordinationOracleControl": {"addr": True},
 "Controller2PC": {"addr": True}
}

def FatTree (arity):
  ncore_switches = (arity / 2) ** 2
  pods = arity
  hosts = []
  links = []
  switches = []
  switches_assigned_so_far = ncore_switches
  hosts_assigned_so_far = 0
  for s in xrange(ncore_switches):
    switches.append('s%d'%s)
  
  for p in xrange(0, pods):
    # Agg singly connected to core
    aggs = []

    for agg in xrange(0, arity / 2):
      aggs.append(agg + switches_assigned_so_far)
      switches.append('s%d'%(agg + switches_assigned_so_far))
      for agg_connect in xrange(0, arity / 2):
        links.append("%s-%s"%(switches[(arity/2)*agg + agg_connect], switches[agg + switches_assigned_so_far]))
    switches_assigned_so_far += (arity/2)
    
    tors = []
    for tor in xrange(0, arity/2):
      tors.append(tor + switches_assigned_so_far)
      switches.append('s%d'%(tor + switches_assigned_so_far))
      for agg in aggs:
        links.append("%s-%s"%((switches[agg], switches[tor + switches_assigned_so_far])))

    switches_assigned_so_far += (arity/2)

    for tor in tors:
      for host in xrange(0, arity / 2):
        hosts.append('h%d'%(host + hosts_assigned_so_far))
        links.append("%s-%s"%(switches[tor], hosts[host + hosts_assigned_so_far]))
      hosts_assigned_so_far += (arity / 2)
  return (hosts, switches, links)

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

if __name__ == "__main__": 
  parser = argparse.ArgumentParser(description="Run this script to generate a YAML setup file with" \
                                   " random network graph")
  parser.add_argument("-n", type=int, help="Arity of fat tree")
  parser.add_argument("-nc", type=int, help="Number of controllers")
  parser.add_argument("-f", dest="file", default="", help="Output file name stem")
  args = parser.parse_args()
  (hosts, switches, links) = FatTree(args.n)
  controllers = random.sample(hosts, args.nc)
  hosts = list(set(hosts) - set(controllers))
  idx = 0 
  for (ct, st, ht, runfile) in config:
    out = WriteGraph(hosts, controllers, switches, links, ct, st, ht, runfile)
    f = open(args.file+str(idx)+".yaml", 'w')
    f.write(yaml.dump(out))
    f.close()
    idx += 1
