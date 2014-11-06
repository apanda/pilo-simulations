import networkx as nx
import numpy.random
import yaml
import sys
import argparse

def Main(n, m, hosts, ctrlrs, stype, htype, ctype, ctrlAddr):
   """Generate a graph with n switches (and m edges per node on average), host hosts
   and controller controllers.
   Hosts and controllers are singly connected"""
   g = nx.erdos_renyi_graph(n, m)
   out = {}
   for node in g.nodes_iter():
     out['s%d'%(node + 1)] = {'type': stype} 
   out['links'] = []
   for (a, b) in g.edges_iter():
     out['links'].append('s%d-s%d'%(a + 1, b + 1))
   for host in xrange(0, hosts):
     host_id = 'h%d'%(host + 1)
     out[host_id] = {'type': htype, 'args':{'address': host + 1}}
     s = numpy.random.randint(n)
     out['links'].append("s%d-%s"%(s+1, host_id))
   for ctrl in xrange(0, ctrlrs):
     ctrl_id = 'c%d'%(ctrl + 1)
     if ctrlAddr:
       out[ctrl_id] = {'type': ctype, 'args':{'address': host + ctrl + 1}}
     else:
       out[ctrl_id] = {'type': ctype}
     s = numpy.random.randint(n)
     out['links'].append("s%d-%s"%(s+1, ctrl_id))
   return yaml.dump(out)

if __name__ == "__main__": 
  # if len(sys.argv) < 9:
  #   print >>sys.stderr, "Usage: %s n m hosts controllers switch_type host_type controller_type ctrl_need_address"%(sys.argv[0])
  #   sys.exit(1)

  parser = argparse.ArgumentParser(description="Run this script to generate a YAML setup file with" \
                                   " random network graph")
  parser.add_argument("-n", type=int, help="number of total switches")
  parser.add_argument("-m", type=int, help="")
  parser.add_argument("-nh", type=int, help="Number of hosts")
  parser.add_argument("-nc", type=int, help="Number of controllers")
  parser.add_argument("-st", help="Switch type: Switch, LSLeaderSwitch")
  parser.add_argument("-ht", help="Host type: Host, HBHost")
  parser.add_argument("-ct", help="Controller type: SpControl, CoordinatingControl, HBControl")
  parser.add_argument("--ctrl-need-addr", dest="if_ctrl_addr", action='store_true', default=False, help="Indicates whether the controllers need addresses")
  args = parser.parse_args()

  print Main(args.n, \
             args.m, \
             args.nh, \
             args.nc, \
             args.st, \
             args.ht, \
             args.ct, \
             args.if_ctrl_addr)
