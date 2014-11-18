from env import *
import networkx as nx

from . import LSLeaderControl, LSGossipControl, HBControl, CoordinatingControl

def WpControlClass(base):
  class WpControl (base):
    def __init__ (self, *args):
      super(WpControl, self).__init__(*args)
      #self.graph = nx.Graph()
      self.hosts = set()
      self.controllers = set([self.name])
      self.waypoint_rules = {}

    # def currentLeader (self, switch):
    #   for c in sorted(list(self.controllers)):
    #     if nx.has_path(self.graph, c, switch):
    #       return c #Find the first connected controller

    def ComputeAndUpdatePaths (self):
      super(WpControl, self).ComputeAndUpdatePaths()
      sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)

      # compute additional paths for waypointing
      for host in self.waypoint_rules.keys():
        (s_wp, d_wp) = self.waypoint_rules[host]
        if s_wp:
          # all packets from this host must be routed to s_wp first
          for host2 in self.hosts:
            if host2 == host:
              continue
            p = MarkedSourceDestPacket(host.address, host2.address)
            path = zip(sp[host.name][s_wp], \
                       sp[host.name][s_wp][1:])
            for (a, b) in path:
              link = self.graph[a][b]['link']
              if self.currentLeader(a) == self.name:
                self.UpdateRules(a, [(p.pack(), link)])

          for host2 in self.hosts:
            if host2 == host:
              continue
            p = MarkedSourceDestPacket(host.address, host2.address)
            p.set_mark()
            path = zip(sp[s_wp][host2.name], \
                       sp[s_wp][host2.name][1:])
            for (a, b) in path:
              link = self.graph[a][b]['link']
              if self.currentLeader(a) == self.name:
                self.UpdateRules(a, [(p.pack(), link)])

        if d_wp:
          # all packets to this host must be routed to d_wp first
          for host2 in self.hosts:
            if host2 == host:
              continue
            p = MarkedSourceDestPacket(host2.address, host.address)
            path = zip(sp[host2.name][d_wp], \
                       sp[host2.name][d_wp][1:])
            for (a, b) in path:
              link = self.graph[a][b]['link']
              if self.currentLeader(a) == self.name:
                self.UpdateRules(a, [(p.pack(), link)])

          for host2 in self.hosts:
            if host2 == host:
              continue
            p = MarkedSourceDestPacket(host2.address, host.address)
            p.set_mark()
            path = zip(sp[d_wp][host.name], \
                       sp[d_wp][host.name][1:])
            for (a, b) in path:
              link = self.graph[a][b]['link']
              if self.currentLeader(a) == self.name:
                self.UpdateRules(a, [(p.pack(), link)])

    def changeWaypointRules(self, new_rules):
      delay = self.ctx.config.ControlLatency

      sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
      self.waypoint_rules = new_rules
      for n in self.graph.nodes():
        if self.currentLeader(n) == self.name:
          self.ctx.schedule_task(delay, lambda: self.updateWaypointRules(n, new_rules))

      self.ComputeAndUpdatePaths()

    def updateWaypointRules(self, switch, new_rules):
      self.waypoint_rules = new_rules
      cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.UpdateWaypointRules, new_rules)
      self.cpkt_id += 1
      self.sendControlPacket(cpacket)
    
  return WpControl
