import networkx as nx
import numpy.random
import yaml
import sys

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
  if len(sys.argv) < 9:
    print >>sys.stderr, "Usage: %s n m hosts controllers switch_type host_type controller_type ctrl_need_address"%(sys.argv[0])
    sys.exit(1)
  print Main(int(sys.argv[1]), \
             int(sys.argv[2]), \
             int(sys.argv[3]), \
             int(sys.argv[4]), \
             sys.argv[5], \
             sys.argv[6], \
             sys.argv[7], \
             bool(sys.argv[8]))
