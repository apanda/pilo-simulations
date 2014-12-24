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

def FatTree (start_switch, start_host, arity):
  ncore_switches = (arity / 2) ** 2
  pods = arity
  hosts = []
  links = []
  switches = []
  hosts_assigned_so_far = start_host
  for s in xrange(ncore_switches):
    switches.append('s%d'%(start_switch + s))
  switches_assigned_so_far = start_switch + ncore_switches
  
  for p in xrange(0, pods):
    # Agg singly connected to core
    aggs = []

    for agg in xrange(0, arity / 2):
      aggs.append(agg + switches_assigned_so_far)
      switches.append('s%d'%(agg + switches_assigned_so_far))
      for agg_connect in xrange(0, arity / 2):
        links.append("%s-%s"%(switches[(arity/2)*agg + agg_connect], \
                switches[agg + switches_assigned_so_far - start_switch]))
    switches_assigned_so_far += (arity/2)
    
    tors = []
    for tor in xrange(0, arity/2):
      tors.append(tor + switches_assigned_so_far)
      switches.append('s%d'%(tor + switches_assigned_so_far))
      for agg in aggs:
        links.append("%s-%s"%((switches[agg - start_switch], \
             switches[tor + switches_assigned_so_far - start_switch])))

    switches_assigned_so_far += (arity/2)

    for tor in tors:
      for host in xrange(0, arity / 2):
        hosts.append('h%d'%(host + hosts_assigned_so_far))
        links.append("%s-%s"%(switches[tor - start_switch], hosts[host + hosts_assigned_so_far - start_host]))
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
  parser.add_argument("-nc", type=int, help="Number of controllers per partition")
  parser.add_argument("-r", type=int, help="Number of partitions (repeated instances of fat tree)")
  parser.add_argument("-f", dest="file", default="", help="Output file name stem")
  args = parser.parse_args()
  all_controllers = []
  all_hosts = []
  all_switches = []
  all_links = []
  nswitches = 0
  nhosts = 0
  partition_switches = []
  for p in xrange(args.r):
    (hosts, switches, links) = FatTree(nswitches, nhosts, args.n)
    nswitches += len(switches)
    nhosts += len(hosts)
    controllers = random.sample(hosts, args.nc)
    hosts = list(set(hosts) - set(controllers))
    all_hosts.extend(hosts)
    all_controllers.extend(controllers)
    all_switches.extend(switches)
    all_links.extend(links)
    for partition in partition_switches:
      sw = random.choice(partition)
      sw2 = random.choice(switches)
      all_links.append("%s-%s"%(sw, sw2))
    partition_switches.append(switches)

  idx = 0 
  for (ct, st, ht, runfile) in config:
    out = WriteGraph(all_hosts, all_controllers, all_switches, all_links, ct, st, ht, runfile)
    f = open(args.file+str(idx)+".yaml", 'w')
    f.write(yaml.dump(out))
    f.close()
    idx += 1
