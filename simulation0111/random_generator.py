import networkx as nx
import numpy.random
import yaml
import sys
import argparse
import matplotlib

config = [
   # Controller type, switch type, host type
   ("LSLeaderControl", "LSLeaderSwitch", "Host", "controllers"),
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

def draw_graph(out, gfile):
   matplotlib.use('Agg')
   import matplotlib.pyplot as plt
   G = nx.Graph()
   for key in out:
      if key == "runfile" or key == "fail_links" or key == "crit_links":
         continue
      if key == "links":
         links = out[key]
         for l in links:
            p = l.split('-')
            G.add_edge(p[1], p[0], type="link")
      else:
         G.add_node(key, node_type=out[key]['type'])
   pos = nx.spring_layout(G)
   nl = [x[0] for x in G.nodes(data=True) if x[1]['node_type'].find("Switch") >= 0]
   nx.draw_networkx_nodes(G,pos,nodelist=nl,node_color="#A0CBE2")
   nl = [x[0] for x in G.nodes(data=True) if x[1]['node_type'].find("Control") >= 0]
   nx.draw_networkx_nodes(G,pos,nodelist=nl,node_color="red")
   nl = [x[0] for x in G.nodes(data=True) if x[1]['node_type'].find("Host") >= 0]
   nx.draw_networkx_nodes(G,pos,nodelist=nl,node_color="green")
   nx.draw_networkx_edges(G,pos,width=1.0,alpha=0.5)
   labels = {}
   for x in G.nodes(data=True):
      labels[x[0]] = x[0]
   nx.draw_networkx_labels(G, pos, labels)
   plt.savefig(gfile)

def find_critical_links(out):
   # for a graph, find the critical links that would cause reachability problems
   # if they fail
   G = nx.Graph()
   for key in out:
      if key == "runfile" or key == "fail_links":
         continue
      if key == "links":
         links = out[key]
         for l in links:
            p = l.split('-')
            G.add_edge(p[1], p[0], type="link")
      else:
         G.add_node(key, node_type=out[key]['type'])
   sp = nx.shortest_paths.all_pairs_shortest_path(G)
   
   crit_links = []
   for (source, paths) in sp.iteritems():
      if source.startswith('h'):
         for (dest, path) in paths.iteritems():
            p = path[1:-1]
            if dest.startswith('h') and source != dest and len(p) > 1:
               for idx in xrange(len(p) - 1):
                  l = "%s-%s" % (p[idx], p[idx+1])
                  if l in out["links"] and l not in crit_links:
                     crit_links.append(l)
   return crit_links

def gen_graph(g, n, m, hosts, ctrlrs, stype, htype, ctype, runfile, gfile, s1, s2, flinks, pnodes):
   """Generate a graph with n switches (and m edges per node on average), host hosts
   and controller controllers.
   Hosts and controllers are singly connected"""
   out = {"runfile": runfile}
   for node in g.nodes_iter():
      sname = 's%d'%(node + 1)
      out[sname] = {'type': stype} 
      if stype in config_args:
         out[sname]['args'] = {}
         for key in config_args[stype]:
            out[sname]['args'][key] = config_args[stype][key]
   out['links'] = []
   for (a, b) in g.edges_iter():
      out['links'].append('s%d-s%d'%(a + 1, b + 1))

   numpy.random.seed(s1)
   for host in xrange(0, hosts):
      host_id = 'h%d'%(host + 1)
      out[host_id] = {'type': htype, 'args':{'address': host + 1}}
      if htype in config_args:
         for key in config_args[htype]:
            out[host_id]['args'][key] = config_args[htype][key]
      s = numpy.random.randint(n)
      out['links'].append("s%d-%s"%(s+1, host_id))
   #ctrlr_per_partition = min(1, ctrlrs/len(pnodes))
   numpy.random.seed(s2)
   for ctrl in xrange(0, ctrlrs):
      ctrl_id = 'c%d'%(ctrl + 1)
      out[ctrl_id] = {'type': ctype}
      if ctype in config_args:
         out[ctrl_id]['args'] = {}
         for key in config_args[ctype]:
            if key == 'addr':
               out[ctrl_id]['args']['address'] = host + ctrl + 1
            else:
               out[ctrl_id]['args'][key] = config_args[ctype][key]
      # assign controllers to partitions in order
      partition_for_ctrl = ctrl % len(pnodes)
      s = numpy.random.randint(len(partition_nodes[partition_for_ctrl]))
      s = partition_nodes[partition_for_ctrl][s]
      out['links'].append("s%d-%s"%(s+1, ctrl_id))

   if flinks:
      out['fail_links'] = flinks
   else:
      out['fail_links'] = out['links']

   return out

def fixGraph(_g):
  """A lot of our graphs are disconnected, it makes sense to reconnected"""
  while (nx.number_connected_components(_g) > 1):
    components = nx.connected_components(_g)
    count = 0
    nodes = []
    for c in components:
       nodes.append(numpy.random.choice(c))
       count += 1
       if count == 2:
          break
    #nodeB = numpy.random.choice(componentB)
    _g.add_edge(nodes[0], nodes[1])

if __name__ == "__main__": 
   parser = argparse.ArgumentParser(description="Run this script to generate a YAML setup file with" \
                                    " random network graph")
   parser.add_argument("-n", type=int, help="number of total switches")
   parser.add_argument("-m", type=int, help="number of average edges per node")
   parser.add_argument("-nh", type=int, help="Number of hosts")
   parser.add_argument("-nc", type=int, help="Number of controllers")
   parser.add_argument("-f", dest="file", default="", help="Output file name stem")
   parser.add_argument("-g", dest="gfile", default="", help="If enabled, writes visualization of the network to gfile")
   parser.add_argument("-w", dest="waxman", action="store_true", help="Generate Waxman graph") 
   parser.add_argument("-p", type=int, dest="partition", default=1,
                       help="If specified, generates p densely connected components that are loosely connected with few links")
   parser.set_defaults(waxman = False)
   args = parser.parse_args()
   g = nx.erdos_renyi_graph(0, 0)
   partition_size = args.n / args.partition
   partitions = []
   for p in xrange(args.partition):
      _g = None
      if args.waxman:
         _g = nx.waxman_graph(partition_size)
      else:
         _g = nx.erdos_renyi_graph(partition_size, args.m*1.0/args.n)
      # No need to fix graph, we take care of fixing up partitions below.
      #fixGraph(_g)
      partitions.append(_g)

   failure_edges = []
   partition_nodes = []
   for p in partitions:
      before = len(g.nodes())
      g = nx.disjoint_union(g, p)
      partition_nodes.append(g.nodes()[before:])
      while (nx.number_connected_components(g) > 1):
         nodes = []
         for c in nx.connected_components(g):
            nodes.append(numpy.random.choice(c))
         g.add_edge(nodes[0], nodes[1])
         failure_edges.append("s%d-s%d" % (nodes[0] + 1, nodes[1] + 1))

   print failure_edges
   print nx.number_connected_components(g)
   print partition_nodes
   s1 = numpy.random.randint(args.n)
   s2 = numpy.random.randint(args.n)
   idx = 0
   for (ct, st, ht, runfile) in config:
      out = gen_graph(g, args.n, args.m,
                      args.nh, args.nc, \
                      st, ht, ct, runfile, \
                      args.gfile, s1, s2, failure_edges, partition_nodes)
      if args.partition == 1:
         out["fail_links"] = find_critical_links(out)
      f = open(args.file+str(idx)+".yaml", 'w')
      f.write(yaml.dump(out))
      f.close()
      idx += 1

   if args.gfile != "":
      draw_graph(out, args.gfile)

