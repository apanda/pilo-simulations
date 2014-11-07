import networkx as nx
import numpy.random
import yaml
import sys
import argparse
import matplotlib

config = [
   # Controller type, switch type, host type
   ("SpControl", "LSLeaderSwitch", "Host"),
   ("CoordinatingControl", "LS2PCSwitch", "Host"),
   ("HBControl", "HBSwitch", "HBHost"), 
]

config_args =  \
{"HBControl": {"epoch": 5000, "send_rate": 200, "addr": True},
 "HBSwitch": {"epoch": 5000, "send_rate": 200},
 "HBHost": {"epoch": 5000, "send_rate": 200},
 "SpControl": {"addr": True},
 "CoordinatingControl": {"addr": True},
}

def draw_graph(out, gfile):
   matplotlib.use('Agg')
   import matplotlib.pyplot as plt
   G = nx.Graph()
   for key in out:
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

def gen_graph(g, n, m, hosts, ctrlrs, stype, htype, ctype, gfile, s1, s2):
   """Generate a graph with n switches (and m edges per node on average), host hosts
   and controller controllers.
   Hosts and controllers are singly connected"""
   out = {}
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

   numpy.random.seed(s2)
   for ctrl in xrange(0, ctrlrs):
      ctrl_id = 'c%d'%(ctrl + 1)
      out[ctrl_id] = {'type': ctype}
      if ctype in config_args:
         out[ctrl_id]['args'] = {}
         for key in config_args[ctype]:
            if 'addr' in config_args[ctype]:
               out[ctrl_id]['args']['address'] = host + ctrl + 1
            else:
               out[ctrl_id]['args'][key] = config_args[ctype][key]
      s = numpy.random.randint(n)
      out['links'].append("s%d-%s"%(s+1, ctrl_id))
         
   return out

if __name__ == "__main__": 
   parser = argparse.ArgumentParser(description="Run this script to generate a YAML setup file with" \
                                    " random network graph")
   parser.add_argument("-n", type=int, help="number of total switches")
   parser.add_argument("-m", type=int, help="number of average edges per node")
   parser.add_argument("-nh", type=int, help="Number of hosts")
   parser.add_argument("-nc", type=int, help="Number of controllers")
   parser.add_argument("-f", dest="file", default="", help="Output file name stem")
   parser.add_argument("-g", dest="gfile", default="", help="If enabled, writes visualization of the network to gfile")
   args = parser.parse_args()
   
   g = nx.erdos_renyi_graph(args.n, args.m*1.0/args.n)
   s1 = numpy.random.randint(args.n)
   s2 = numpy.random.randint(args.n)
   idx = 0
   for (ct, st, ht) in config:
      out = gen_graph(g, args.n, args.m,
                      args.nh, args.nc, \
                      st, ht, ct,
                      args.gfile, s1, s2)
      
      f = open(args.file+str(idx)+".yaml", 'w')
      f.write(yaml.dump(out))
      f.close()
      idx += 1

   if args.gfile != "":
      draw_graph(out, args.gfile)
