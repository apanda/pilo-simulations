from env import *
import networkx as nx

from . import LSLeaderControl, LSGossipControl, HBControl, CoordinatingControl
import copy

BANDWIDTH_LIMIT = 10

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
          if host.address == rule["source"] and h2.address == rule["dest"]:
            bw_goal = rule["bw"]
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


class LBBandwidthController(object):
  def __init__ (self):
    self.lb_rules = []

  def AddLBRules(self, rules):
    self.lb_rules = rules

  def ComputePaths(self):
    rules_copy = []

    for rule in self.lb_rules:
      sname = rule["sname"]
      dname = rule["dname"]
      all_tunnel_groups = []

      if sname in self.graph.nodes() and dname in self.graph.nodes():
        for path in nx.all_simple_paths(self.graph, sname, dname):
          all_tunnel_groups.append(path[1:-1])
        rules_copy.append({})
        rules_copy[-1]["sname"] = sname
        rules_copy[-1]["dname"] = dname
        rules_copy[-1]["preference"] = all_tunnel_groups
        rules_copy[-1]["bw"] = rule["bw"]
        rules_copy[-1]["source"] = rule["source"]
        rules_copy[-1]["dest"] = rule["dest"]
        rules_copy[-1]["encap"] = rule["encap"]

    if rules_copy == {}:
      return {}

    ret = {}
    allocation = {}
    for edge in self.graph.edges():
      allocation[self.graph[edge[0]][edge[1]]['link']] = {"total": 0}

    total_paths = {}
    fg_bw_info = {}

    #print rules_copy
    while True:
      stop = True
      for rule in rules_copy:
        if rule["bw"] > 0 and len(rule["preference"]) > 0:
          stop = False
          break
      if stop:
        #print "breaking out of loop"
        break

      temp_alloc = {}
      current_paths = {}

      for rule in rules_copy:
        # attempts to allocate the links in order of preference
        #print rule["sname"], rule["dname"], rule["bw"], len(rule["preference"])
        if "preference" in rule and len(rule["preference"]) > 0 and rule["bw"] > 0:
          counter = 0
          path_edges = None
          for path in rule["preference"]:
            path_edges = zip(path, path[1:])
            min_bw = BANDWIDTH_LIMIT

            for e in path_edges:
              l = self.graph[e[0]][e[1]]['link']
              if l:
                bw_usage = allocation[l]["total"]
                assert(bw_usage >= 0 and bw_usage <= BANDWIDTH_LIMIT)
                if min_bw > (BANDWIDTH_LIMIT - bw_usage):
                  min_bw = BANDWIDTH_LIMIT - bw_usage

            if min_bw == 0:
              counter += 1
              continue
            break

          if counter >= len(rule["preference"]):
            rule["preference"] = []
            continue
          else:
            rule["preference"] = rule["preference"][counter+1:]
          
          # found a flow path that has bandwidth left
          # if this link is being used by another flow group in this round, split evenly

          current_paths[(rule["source"], rule["dest"])] = []
          cur_path = current_paths[(rule["source"], rule["dest"])]

          for e in path_edges: 
            l = self.graph[e[0]][e[1]]['link']
            if l not in temp_alloc:
              temp_alloc[l] = 0

            temp_alloc[l] += 1
            cur_path.append(e)

      # processing all of the current paths in this iteration, updating bandwidth along the way
      allocation_update = {}
      for (e, d) in allocation.iteritems():
        allocation_update[e] = {"total": allocation[e]["total"]}      

      for (fg, path) in current_paths.iteritems():
        for rule in rules_copy:
          if rule["source"] == fg[0] and rule["dest"] == fg[1]:
            break

        if rule["bw"] == 0:
          continue
        min_bw = min(BANDWIDTH_LIMIT, rule["bw"])
        #print fg, min_bw
        for e in path:
          l = self.graph[e[0]][e[1]]['link']
          bw = (BANDWIDTH_LIMIT - allocation[l]["total"]) * 1.0 /temp_alloc[l]
          #print e, allocation[l]["total"], temp_alloc[l], rule["bw"], bw
          min_bw = min(bw, min_bw)

        if fg not in total_paths:
          total_paths[fg] = 0
        total_paths[fg] += 1

        for (a, b) in path:
          link = self.graph[a][b]['link']
          allocation_update[link]["total"] += min_bw
          sd_pkt = SourceDestinationPacket(rule["source"], rule["dest"])
          tunnel_id = total_paths[fg]
          p = EncapSourceDestPacket(tunnel_id, sd_pkt)
          if a not in ret:
            ret[a] = []
          ret[a].append((p.pack(), link))
          
        if fg not in fg_bw_info:
          fg_bw_info[fg] = []

        for rule2 in self.lb_rules:
          if rule2["source"] == rule["source"] and rule2["dest"] == rule["dest"]:
            fg_bw_info[fg].append(min_bw * 100.0 / rule2["bw"])
            break
        #print "FG: ", fg
        #print "MIN bw:", min_bw
        #print "PATH:", path

        rule["bw"] -= min_bw
      for (e, d) in allocation_update.iteritems():
        allocation[e]["total"] = d["total"]
      #print "iteration done"

    for (fg, l) in fg_bw_info.iteritems():
      for rule in rules_copy:
        if rule["source"] == fg[0] and rule["dest"] == fg[1]:
          #print "Subtracting:", rule["bw"], min_bw
          sd_pkt = SourceDestinationPacket(rule["source"], rule["dest"])
          p = EncapSourceDestPacket(0, sd_pkt)
          ret[rule["encap"]].append((p.info(), l))
          
    #print fg_bw_info
    #print self, total_paths
    #raw_input()
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    for host in self.hosts:
      for h2 in self.hosts:
        if host == h2:
          continue
        if h2.name in sp[host.name]:
          p = SourceDestinationPacket(host.address, h2.address)
          path = zip(sp[host.name][h2.name], \
                    sp[host.name][h2.name][1:])
          for (a, b) in path[1:]:
            link = self.graph[a][b]['link']
            if a not in ret:
              ret[a] = []
            ret[a].append((p.pack(), link))

    #print [(k, v) for (k, v) in allocation.items() if v != {}]
    return ret

          
def LBControllerClass(base_class):
  class RetClass(base_class, LBBandwidthController):
    def __init__(self, name, ctx, address):
      base_class.__init__(self, name, ctx, address)
      LBBandwidthController.__init__(self)

    def ComputeAndUpdatePaths(self):
      all_rules = LBBandwidthController.ComputePaths(self)
      for switch, rules in all_rules.iteritems():
        if self.currentLeader(switch):
          for r in rules:
            self.UpdateRules(switch, [r])

  return RetClass
