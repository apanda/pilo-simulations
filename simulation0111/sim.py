from env import *
import networkx as nx
import yaml
import sys
from itertools import permutations

"""A mechanism to run simulations on a particular trace. The command can be run as
   python simulator.py format.yaml trace check_simulation_hbldr
   format.yaml is the topology
   trace is an event trace
   check_simulation_hbldr is an additional Python file that needs to be imported for
   the controller code"""

class Simulation (object):
  __metaclass__ = Singleton
  """Represents a simulation being run"""
  def __init__ (self):
    self.unaccounted_packets = list()
    self.sent_packet_time = {}
    self.hosts = []
    self.latency_at_time = {}
    self.packets_sent = 0
    self.packets_recved = 0
    self.reachability_at_time = {}
    # A mechanism for oracles to get a hold of the current graph
    self.graph = nx.Graph()  
    self.host_names = []
    self.switch_names = []
    self.controller_names = []

  def Clear (self):
    self.unaccounted_packets = list()
    self.sent_packet_time = {}
    self.hosts = []
    self.latency_at_time = {}
    self.packets_sent = 0
    self.packets_recved = 0
    self.reachability_at_time = {}
    # A mechanism for oracles to get a hold of the current graph
    self.graph = nx.Graph()  
    self.host_names = []
    self.switch_names = []
    self.controller_names = []
    self.ctx = None

  def HostSendCallback (self, switch, packet):
    self.packets_sent += 1 
    self.unaccounted_packets.append(packet)
    self.sent_packet_time[packet] = switch.ctx.now

  def HostRecvCallback (self, switch, packet):
    self.packets_recved += 1
    self.unaccounted_packets.remove(packet)
    print "%f pkt_recv latency %f"%(switch.ctx.now, switch.ctx.now - self.sent_packet_time[packet])
    self.latency_at_time[self.sent_packet_time[packet]] = switch.ctx.now - self.sent_packet_time[packet]
  
  def Send(self, host, src, dest):
    print "%f sending %d %d"%(self.ctx.now, src, dest)
    p = SourceDestinationPacket(src, dest)
    self.objs[host].Send(p)
    #self.ctx.schedule_task(time, lambda: objs[host].Send(p))
  
  def scheduleSend (self, time, host, src, dest):
    self.ctx.schedule_task(time, lambda: self.Send(host, src, dest))
  def scheduleLinkUp (self, time, link):
    def LinkUpFunc ():
      self.graph.add_edge(*link.split("-"))
      self.link_objs[link].SetUp()
    self.ctx.schedule_task(time, LinkUpFunc)
  def scheduleLinkDown (self, time, link):
    def LinkDnFunc ():
      self.graph.remove_edge(*link.split("-"))
      self.link_objs[link].SetDown()
    self.ctx.schedule_task(time, LinkDnFunc)
  
  def checkAllPaths (self):
    """For now this assumes singly homed hosts"""
    if self.ctx.now <= 0.0:
      return
    tried = 0
    connected = 0
    for (ha, hb) in permutations(self.hosts, 2):
      #print "%f Trying %s %s"%(self.ctx.now, ha.name, hb.name)
      # Don't think there is anything really faster than walking the
      # path here
      visited = [ha]
      assert(len(ha.links) <= 1) # No link or one link
      assert(len(hb.links) <= 1) # No link or one link
      latencies = []
      if nx.has_path(self.graph, ha.name, hb.name):
        tried += 1
        # At least connected to the network, improve this
        pkt = SourceDestinationPacket(ha.address, hb.address)
        if (len(ha.links) == 0):
          continue
        link = list(ha.links)[0]
        current = link.a if link.a != ha else link.b
        length = 0
        while current != hb and current not in visited:
          length += 1
          visited.append(current)
          if pkt.pack() not in current.rules:
            #print "%f %s %s not connected at %s, path %s (no rule)"%(self.ctx.now, ha.name, hb.name, current.name, visited)
            break
          link = current.rules[pkt.pack()]
          if not link.up:
            #print "%f %s %s not connected at %s, path %s (link down %s)"%(self.ctx.now, ha.name, hb.name, current.name, \
                    #visited, link)
            break
          current = link.a if link.a != current else link.b
        if current == hb:
          #print "%f %s %s connected"%(self.ctx.now, ha.name, hb.name)
          connected += 1
          latencies.append(sum(map(lambda c: self.ctx.config.DataLatency, range(length))))
        else:
          #print "%f %s %s not connected at %s, path %s"%(self.ctx.now, ha.name, hb.name, current.name, visited)
          pass
    if tried > 0:
      self.reachability_at_time[self.ctx.now] = (tried, connected, latencies)

  def Setup (self, simulation_setup, trace):
    self.ctx = Context()

    setup = yaml.load(simulation_setup)
    other_includes = setup['runfile']
    other = __import__ (other_includes)
    for l in dir(other):
      if not l.startswith('__'):
        globals()[l] = other.__getattribute__(l)

    del setup["runfile"]
    links = setup['links']
    del setup['links']
    self.objs = {}
    for s, d in setup.iteritems():
      self.objs[s] = eval(d['type'])(s, self.ctx, **d['args']) if 'args' in d \
                       else eval(d['type'])(s, self.ctx)
      self.graph.add_node(s)
      if isinstance(self.objs[s], ControllerTrait):
        self.controller_names.append(s)
      elif isinstance(self.objs[s], HostTrait):
        self.objs[s].send_callback = self.HostSendCallback
        self.objs[s].recv_callback = self.HostRecvCallback
        self.hosts.append(self.objs[s])
        self.host_names.append(s)
      else:
        self.switch_names.append(s)
    self.link_objs = {}
    for l in links:
      p = l.split('-')
      self.link_objs[l] = Link(self.ctx, self.objs[p[0]], self.objs[p[1]])
      self.link_objs['%s-%s'%(p[1], p[0])] = self.link_objs[l]
    for ev in trace:
      if ev.startswith("//"):
        continue
      parts = ev.strip().split()
      time = float(parts[0])
      if "-" in parts[1]:
        # Dealing with a link
        link = parts[1]
        if parts[2] == 'up':
          self.scheduleLinkUp(time, link)
        elif parts[2] == 'down':
          self.scheduleLinkDown(time, link)
        else:
          print "Unknown request"
      elif parts[1] == 'end':
        # End of simulation time.
        self.ctx.final_time = time
      else:
        # Dealing with host
        host = parts[1]
        if parts[2] == "send":
          addr_a = int(parts[3])
          addr_b = int(parts[4])
          self.scheduleSend(time, host, addr_a, addr_b)
        else:
          print "Unknown request"

  def Run (self):
    self.ctx.post_task_check = self.checkAllPaths
    print "Starting replay"
    self.ctx.run()
    print "Done replay, left %d items"%(self.ctx.queue.qsize()) 

  def Report (self, show_converge):
    if self.packets_sent > 0:
      print "%f %d packets sent total %d recved (Loss %f%%)"%(self.ctx.now, \
                                   self.packets_sent, \
                                   self.packets_recved, \
                                   (float(self.packets_sent - self.packets_recved)/ float(self.packets_sent)) * 100.0)
      print "Latency"
      for t in sorted(self.latency_at_time.keys()):
        print "%f %f"%(t, self.latency_at_time[t]) 
    
    print "Convergence"
    if show_converge:
      for t in sorted(self.reachability_at_time.keys()):
        (tried, reachable) = self.reachability_at_time[t][:2]
        rest  = self.reachability_at_time[t][2:] 
        perc = (float(reachable) * 100.0)/tried
        print "%f %d %d %f %s"%(t, \
                tried, \
                reachable, \
                perc, \
                ' '.join(map(str, rest)))

