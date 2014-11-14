import networkx as nx
import yaml
import sys
from itertools import permutations
def CheckAllHostConnectivity (pairs, g):
  matrix = nx.all_pairs_shortest_path_length(g)
  connected = 0
  for (a, b) in pairs:
    if b in matrix[a]:
      connected += 1
  return connected

if len(sys.argv) < 3:
  print >>sys.stderr, "Usage: %s topo trace"
  sys.exit(1)
f = open(sys.argv[1])
x = f.read()
setup = yaml.load(x)
g = nx.Graph()
links = setup['links']
del setup['links']
hosts = []
for s in setup.keys():
  if s.startswith('h'):
    hosts.append(s)
  g.add_node(s)
all_pairs = list(permutations(hosts, 2))
connectivity = {}
tr = open(sys.argv[2])
for t in tr:
  p = t.strip().split()
  time = float(p[0])
  relevant = True
  if p[-1] == "up":
    nodes = p[1].split('-')
    g.add_edge(nodes[0], nodes[1])
    relevant = True
  elif p[-1] == "down":
    nodes = p[1].split('-')
    g.remove_edge(nodes[0], nodes[1])
    relevant = True
  if relevant:
    connected = CheckAllHostConnectivity(all_pairs, g)
    connectivity[time] = connected
for time in sorted(connectivity.keys()):
  print "%f %d %d %f"%(time, connectivity[time], len(all_pairs), \
          (float(connectivity[time])/float(len(all_pairs))) * 100.0)
