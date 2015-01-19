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


class LBController(object):
  def __init__ (self):
    self.lb_rules = []

  def AddLBRules(self, fg):
    self.lb_rules = fg

  def ComputePaths(self):
    rules = {}
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)

    for host in self.hosts:
      for h2 in self.hosts:
        if host == h2:
          continue

        for rule in self.lb_rules:
          print "computing lb_rules", host.address, h2.address, self.lb_rules
          if host.address == rule["source"] and h2.address == rule["dest"]:
            all_tunnel_groups = []
            for path in nx.all_simple_paths(self.graph, host.name, h2.name):
              all_tunnel_groups.append(path)

            if len(all_tunnel_groups) == 0:
              continue
            elif len(all_tunnel_groups) == 1:
              tg = all_tunnel_groups * 2
            else:
              all_tunnel_groups = sorted(all_tunnel_groups, key=lambda p: len(p))
              tg = all_tunnel_groups[:2]

            print "tunnel group", tg
            tunnel_id = 0
            for s in tg:
              p = SourceDestinationPacket(host.address, h2.address)
              ep = EncapSourceDestPacket(tunnel_id, p)
              path = zip(s, s[1:])
              for (a, b) in path:
                if a not in rules:
                  rules[a] = []
                link = self.graph[a][b]['link']
                rules[a].append((ep.pack(), link))
              tunnel_id += 1

        if h2.name in sp[host.name]:
          p = SourceDestinationPacket(host.address, h2.address)
          path = zip(sp[host.name][h2.name], \
                    sp[host.name][h2.name][1:])
          for (a, b) in path[1:]:
            link = self.graph[a][b]['link']
            if a not in rules:
              rules[a] = []
            rules[a].append((p.pack(), link))
    return rules
          
def LBControllerClass(base_class):
  class RetClass(base_class, LBController):
    def __init__(self, name, ctx, address):
      base_class.__init__(self, name, ctx, address)
      LBController.__init__(self)

    def ComputeAndUpdatePaths(self):
      all_rules = LBController.ComputePaths(self)
      for switch, rules in all_rules.iteritems():
        if self.currentLeader(switch):
          for r in rules:
            self.UpdateRules(switch, [r])

  return RetClass
