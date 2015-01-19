from env import *
import networkx as nx
import yaml
import sys
from itertools import permutations, chain, imap
import numpy.random as random
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
    self.sent_packet_host = {}
    self.hosts = []
    self.address_to_host = {}
    self.latency_at_time = {}
    self.rule_changes = []
    self.packets_sent = 0
    self.packets_recved = 0
    self.reachability_at_time = {}
    self.count_ctrl_packets = {}
    # A mechanism for oracles to get a hold of the current graph
    self.graph = nx.Graph()  
    self.host_names = []
    self.switch_names = []
    self.controller_names = []
    self.check_always = True
    self.latency_check = False
    self.policy = None

  def Clear (self):
    self.objs = {}
    self.unaccounted_packets = list()
    self.sent_packet_time = {}
    self.hosts = []
    self.address_to_host = {}
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

  def HostSendCallback (self, host, packet):
    if packet not in self.sent_packet_time:
      self.packets_sent += 1 
      self.unaccounted_packets.append(packet)
      self.sent_packet_time[packet] = host.ctx.now
      self.sent_packet_host[packet] = host
      self.latency_at_time[host.ctx.now] = []

  def HostRecvCallback (self, switch, packet):
    self.packets_recved += 1
    self.unaccounted_packets.remove(packet)
    self.latency_at_time[self.sent_packet_time[packet]].append( switch.ctx.now - self.sent_packet_time[packet])

  def DropCallback (self, switch, source, packet):
    if packet in self.sent_packet_time:
      # Resend if physically connected
      if nx.has_path(self.graph, self.sent_packet_host[packet].name, self.address_to_host[packet.destination]):
        self.sent_packet_host[packet].Send(packet)
      else:
        self.unaccounted_packets.remove(packet)

  def CountCtrlCallback(self, name, mtype):
    if name not in self.count_ctrl_packets:
      self.count_ctrl_packets[name] = {}
    if mtype not in self.count_ctrl_packets[name]:
      self.count_ctrl_packets[name][mtype] = 0
    self.count_ctrl_packets[name][mtype] += 1
  
  def Send(self, host, src, dest):
    #print "%f sending %d %d"%(self.ctx.now, src, dest)
    # To reduce memory pressure, only send if src and dest are connected
    if nx.has_path(self.graph, host, self.address_to_host[dest]):
      p = SourceDestinationPacket(src, dest)
      self.objs[host].Send(p)
      #self.ctx.schedule_task(time, lambda: objs[host].Send(p))

  def scheduleCheck (self, time):
    self.ctx.schedule_task(time, self.checkAllPaths)

  def scheduleSend (self, time, host, src, dest):
    self.ctx.schedule_task(time, lambda: self.Send(host, src, dest))

  def computeAndInstallPaths (self):
    paths = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    for (ha, hb) in permutations(self.host_names, 2):
      if hb in paths[ha]:
        ha_addr = self.objs[ha].address
        hb_addr = self.objs[hb].address
        pkt = SourceDestinationPacket(ha_addr, hb_addr)
        path = paths[ha][hb][1:]
        for p in xrange(len(path) - 1):
          link = self.link_objs["%s-%s"%(path[p], path[p+1])]
          self.objs[path[p]].rules.update([(pkt.pack(), link)])
  
  def allUsedLinks (self):
    # Compute the set of all links currently in use.
    switches = map(lambda s: self.objs[s], self.switch_names)
    links = list(chain.from_iterable(imap(lambda s: s.rules.values(), switches)))
    return list(set(links))

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
  
  def scheduleUsedLinkDown (self, time, uptime):
    # Schedule a link currently in use to come down and then up
    def LinkDnFunc ():
      links = self.allUsedLinks()
      links = filter(lambda l: ((l.up) and (l.a not in self.hosts) and (l.b not in self.hosts)), links)
      if len(links) == 0:
        print "%f link down requested no link found"%(self.ctx.now)
        return
      link = random.choice(links)
      self.graph.remove_edge(*str(link).split("-"))
      print "%f failing %s"%(self.ctx.now, str(link))
      print "%f repairing %s"%(self.ctx.now + uptime, str(link))
      link.SetDown()
      self.scheduleLinkUp(uptime, str(link))
    self.ctx.schedule_task(time, LinkDnFunc) 

  def scheduleOracleCompute (self, time):
    self.ctx.schedule_task(time, self.computeAndInstallPaths)

  def countPacketsPerLink (self):
    total_control_packets = {}
    d = {1: "ForwardPacket",
         2: "UpdateRules",
         3: "NotifySwitchUp",
         4: "NotifyLinkDown",
         5: "NotifyLinkUp",
         6: "PacketIn",
         7: "GetSwitchInformation",
         8: "SwitchInformation",
         9: "SetSwitchLeader",
         10: "AckSetSwitchLeader",
         11: "RequestRelinquishLeadership",
         12: "AckRelinquishLeadership",
         "ALL": "AllCtrlId",
         13: "UpdateWaypointRules",
         14: "Propose",
         15: "Accept",
         16: "Decide",
         17: "ProposeReply",
         18: "AcceptReply",
         19: "PaxosMaxSeq",
         20: "NackUpdateRules",
         21: "ControlAck"
       }

    print "CountPacketsPerLink start"
    for name, l in self.link_objs.iteritems():
      if isinstance(l, BandwidthLink):
        s = 0
        for mtype, count in l.control_packets.iteritems():
          if d[mtype] not in total_control_packets:
            total_control_packets[d[mtype]] = 0
          total_control_packets[d[mtype]] += count
          s += count
        print name, l, l.control_packets, "total:", s

    if len(total_control_packets) > 0:
      print "Total control packets over all links: ", total_control_packets

    for name, l in self.link_objs.iteritems():
      if isinstance(l, BandwidthLink):
        print name, l, "data packets:", l.other_packets

    print "CountPacketsPerLink finish"

    self.ctx.schedule_task(1000, self.countPacketsPerLink)
  
  def checkAllPaths (self):
    """For now this assumes singly homed hosts"""
    if self.ctx.now <= 0.0:
      return
    print "%f checking path"%(self.ctx.now)
    if len(self.count_ctrl_packets) > 0:
      print self.ctx.now, self.count_ctrl_packets
    tried = 0
    connected = 0
    latencies = []
    for (ha, hb) in permutations(self.hosts, 2):
      #print "%f Trying %s %s"%(self.ctx.now, ha.name, hb.name)
      # Don't think there is anything really faster than walking the
      # path here
      visited = [ha]
      assert(len(ha.links) <= 1) # No link or one link
      assert(len(hb.links) <= 1) # No link or one link
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
          if self.latency_check:
            latencies.append(sum(map(lambda c: self.ctx.config.DataLatency, range(length))))
        else:
          #print "%f %s %s not connected at %s, path %s"%(self.ctx.now, ha.name, hb.name, current.name, visited)
          pass
    if tried > 0:
      length = 0
      for g in nx.connected_components(self.graph):
        length += 1
      self.reachability_at_time[self.ctx.now] = (tried, connected, length)

  def RuleChangeNotification (self, name): 
    self.rule_changes.append((self.ctx.now, name))

  def calcConvergeTime(self, t1, t2, converge_time = -1):
    # calculate the exact time that the network becomes stable:
    # switch states and controller states match with the physical network
    converged = True

    # controllers should be consistent with each other and the underlying graph
    for c in self.controller_names:
      ctrl = self.objs[c]
      if not nx.is_isomorphic(self.graph, ctrl.graph):
        converged = False
        cgraph = nx.Graph(ctrl.graph)
        node_diff = set(self.graph.nodes()) - set(cgraph.nodes())
        cgraph.add_nodes_from(list(node_diff))
        node_diff = set(cgraph.nodes()) - set(self.graph.nodes())
        self.graph.add_nodes_from(list(node_diff))
        diff = nx.difference(self.graph, cgraph)
        print "%f %s not converged %s"%(self.ctx.now, ctrl.name, diff.edges())
        #break
      else: 
        print "%f %s converged"%(self.ctx.now, ctrl.name)
    # switches should also be consistent with each other and the controllers
    if converged and self.policy is None:
      c = self.objs[self.controller_names[0]]
      rules = {}
      for s in self.switch_names:
        rules[s] = {}
      sp = nx.shortest_paths.all_pairs_shortest_path(c.graph)
      for host in c.hosts:
        for h2 in c.hosts:
          if h2 == host:
            continue
          if h2.name in sp[host.name]:
            p = SourceDestinationPacket(host.address, h2.address)
            path = zip(sp[host.name][h2.name], \
                       sp[host.name][h2.name][1:])
            for (a, b) in path[1:]:
              link = c.graph[a][b]['link']
              rules[a][p.pack()] = link

      for s in self.switch_names:
        sw = self.objs[s]
        if rules[s] != sw.rules:
          print self.ctx.now, s, len(rules), len(sw.rules)
          converged = False
          break
    elif converged and self.policy['name'] == "load_balancing":
      c = self.objs[self.controller_names[0]]
      correct_rules = c.ComputePaths()

    if converged:
      if converge_time == -1:
        print "CONVERGE_TIME: ", t1, t2, self.ctx.now
        self.ctx.schedule_task(10, lambda: self.calcConvergeTime(t1, t2, self.ctx.now))
      else:
        self.ctx.schedule_task(10, lambda: self.calcConvergeTime(t1, t2, converge_time))
    else:
      self.ctx.schedule_task(10, lambda: self.calcConvergeTime(t1, t2, -1))

  def Setup (self, simulation_setup, trace, 
             retry_send = False, 
             converge_time = True, 
             count_ctrl_packet = False, 
             count_packets = -1):
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
    policy = {}
    if 'policy' in setup:
      policy["name"] = setup['policy']['name']
      policy["args"] = setup['policy']['args']
      del setup['policy']
    if 'fail_links' in setup:
      del setup['fail_links']
    if 'crit_links' in setup:
      del setup['crit_links']
    self.objs = {}
    controller_temp = []
    for s, d in setup.iteritems():
      # hard-coded madness
      if 'name' in policy and policy['name'] == "load_balancing":
          if d['type'] == "LSGossipControl" or d['type'] == "HBControl" \
             or d['type'] == "LSLeaderControl" or d['type'] == "LSPaxosOracleControl" \
             or d['type'] == "CoordinatingOracleControl":
            controller_class = LBControllerClass(eval(d['type']))
            self.objs[s] = controller_class(s, self.ctx, **d['args']) if 'args' in d \
                           else controller_class(s, self.ctx)
            controller_temp.append(self.objs[s])
          elif d['type'] == "LinkStateSwitch" or d['type'] == "LS2PCSwitch":
            switch_class = LBSwitchClass(eval(d['type']))
            self.objs[s] = switch_class(s, self.ctx, **d['args']) if 'args' in d \
                           else switch_class(s, self.ctx)
          else:
            self.objs[s] = eval(d['type'])(s, self.ctx, **d['args']) if 'args' in d \
                           else eval(d['type'])(s, self.ctx)
      else:
        self.objs[s] = eval(d['type'])(s, self.ctx, **d['args']) if 'args' in d \
                       else eval(d['type'])(s, self.ctx)

      self.graph.add_node(s)
      if isinstance(self.objs[s], ControllerTrait):
        self.controller_names.append(s)
        if count_ctrl_packet:
          self.objs[s].ctrl_callback = self.CountCtrlCallback
      elif isinstance(self.objs[s], HostTrait):
        self.objs[s].send_callback = self.HostSendCallback
        self.objs[s].recv_callback = self.HostRecvCallback
        self.hosts.append(self.objs[s])
        self.host_names.append(s)
        self.address_to_host[self.objs[s].address] = s
      else:
        self.switch_names.append(s)
        if retry_send:
          self.objs[s].drop_callback = self.DropCallback
        self.objs[s].rule_change_notification = self.RuleChangeNotification

    if 'name' in policy and policy['name'] == "load_balancing":
      lb_rules = []
      for source_host, dest_host in policy['args'].iteritems():
        s_addr, d_addr = None, None
        for n, obj in self.objs.iteritems():
          if obj.name == source_host:
            s_addr = obj.address
          if obj.name == dest_host:
            d_addr = obj.address

          for l in links:
            p = l.split('-')
            if p[0] == source_host or p[1] == source_host:
              encap_switch = p[1] if p[0] == source_host else p[0]
              self.objs[encap_switch].role = LoadBalancingSwitch.ENCAP
            elif p[0] == dest_host or p[1] == dest_host:
              decap_switch = p[1] if p[0] == dest_host else p[0]
              self.objs[decap_switch].role = LoadBalancingSwitch.DECAP

        if s_addr is not None and d_addr is not None:
          lb_rules.append({})
          d = lb_rules[-1]
          d["source"] = s_addr
          d["dest"] = d_addr
          d["encap"] = encap_switch
          self.objs[encap_switch].lb_rules.add(s_addr)
          d["decap"] = decap_switch
          self.objs[decap_switch].lb_rules.add(d_addr)

      # installs policy in controllers
      for c in controller_temp:
        c.AddLBRules(lb_rules)
      self.policy = policy

    self.link_objs = {}
    for l in links:
      p = l.split('-')
      if count_packets > -1:
        self.link_objs[l] = BandwidthLink(self.ctx, self.objs[p[0]], self.objs[p[1]], count_packets)
      else:
        self.link_objs[l] = Link(self.ctx, self.objs[p[0]], self.objs[p[1]])
      self.link_objs['%s-%s'%(p[1], p[0])] = self.link_objs[l]

    if count_packets > -1:
      self.ctx.schedule_task(1000, self.countPacketsPerLink)
    first_link_event = None
    last_link_event = None
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
        if converge_time:
          if first_link_event is None:
            first_link_event = time
          last_link_event = time
      elif parts[1] == 'end':
        # End of simulation time.
        self.ctx.final_time = time
      elif parts[1] == 'compute_and_update':
        self.scheduleOracleCompute(time)
      elif parts[1] == 'down_active':
        uptime = float(parts[2])
        self.scheduleUsedLinkDown(time, uptime)
      else:
        # Dealing with host
        host = parts[1]
        if parts[2] == "send":
          addr_a = int(parts[3])
          addr_b = int(parts[4])
          self.scheduleSend(time, host, addr_a, addr_b)
        else:
          print "Unknown request"
    if converge_time:
      print "Scheduling converge time at ", last_link_event
      self.ctx.schedule_task(last_link_event, lambda: self.calcConvergeTime(first_link_event, last_link_event, -1))
  def Run (self):
    if self.check_always:
      self.ctx.post_task_check = self.checkAllPaths
    print "Starting replay"
    self.ctx.run()
    print "Done replay, left %d items"%(self.ctx.queue.qsize()) 

  def Report (self, show_converge):
    print "Messages"
    for c in self.controller_names:
      print "%s"%c
      ctrl_msgs = self.objs[c].update_messages
      for k in sorted(ctrl_msgs.keys()):
        print "    %s %d"%(k, ctrl_msgs[k])
    print "Rule Changes"
    for (t, w) in self.rule_changes:
      print "%f %s change"%(t, w)
    if self.packets_sent > 0:
      print "%f %d packets sent total %d recved (Loss %f%%)"%(self.ctx.now, \
                                   self.packets_sent, \
                                   self.packets_recved, \
                                   (float(self.packets_sent - self.packets_recved)/ float(self.packets_sent)) * 100.0)
      print "Latency"
      for t in sorted(self.latency_at_time.keys()):
        print "%f %s"%(t, ' '.join(map(str, self.latency_at_time[t])))
      # For packets that were never received, record (near) infintite latency
      unaccounted_latency = []
      for p in self.unaccounted_packets:
        unaccounted_latency.append(self.ctx.now - self.sent_packet_time[p])
      print "%f %s"%(self.ctx.now, ' '.join(map(str, unaccounted_latency)))
    
    print "Convergence"
    if show_converge:
      for t in sorted(self.reachability_at_time.keys()):
        (tried, reachable) = self.reachability_at_time[t][:2]
        components = self.reachability_at_time[t][2]
        perc = (float(reachable) * 100.0)/tried
        print "%f %d %d %f %d"%(t, \
                tried, \
                reachable, \
                perc, \
                components)
