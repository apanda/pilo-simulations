from env import *
import networkx as nx
from collections import defaultdict

class LogEntry(object):
  def __init__(self, switch_id, link_id, event_id, state):
    pass

class Log(object):
  def __init__(self, gc_param):
    self.log = {}
    self.gc_param = gc_param

  def add_event(self, switch_id, link_id, event_id, state):
    if switch_id not in self.log:
      self.log[switch_id] = {}
    if link_id not in self.log[switch_id]:
      self.log[switch_id][link_id] = {}
    if event_id not in self.log[switch_id][link_id]:
      self.log[switch_id][link_id][event_id] = state
    
  def iterate(self):
    for switch_id in sorted(self.log.keys()):
      for link_id in sorted(self.log[switch_id].keys()):
        for event_id in sorted(self.log[switch_id][link_id].keys()):
          state = self.log[switch_id][link_id][event_id]
          yield event_id, state

  def get_switches(self):
    return self.log.keys()

  def find_gaps(self, switch_id):
    event_list = {}
    for link_id in sorted(self.log[switch_id].keys()):
      event_list[link_id] = []
      last_event_id = None
      el = sorted(self.log[switch_id][link_id].keys())
      for event_id in el:
        if last_event_id is None:
          event_list[link_id].append(event_id)
        if last_event_id is not None and event_id - last_event_id > 1:
          state = self.log[switch_id][link_id][event_id]
          event_list[link_id].append((last_event_id, event_id))
        if event_id == el[-1]:
          event_list[link_id].append(event_id)
        last_event_id = event_id
    return event_list

  def get_smaller_events(self, switch_id, link_id, low):
    ret = []
    if switch_id in self.log:
      if link_id in self.log[switch_id]:
        for event_id, state in self.log[switch_id][link_id].iteritems():
          if event_id < low:
            ret.append((event_id, state))
    return ret

  def get_larger_events(self, switch_id, link_id, high):
    ret = []
    if switch_id in self.log:
      if link_id in self.log[switch_id]:
        for event_id, state in self.log[switch_id][link_id].iteritems():
          if event_id > high:
            ret.append((event_id, state))
    return ret

  def get_gap_events(self, switch_id, link_id, low, high):
    ret = []
    if switch_id in self.log:
      if link_id in self.log[switch_id]:
        for event_id, state in self.log[switch_id][link_id].iteritems():
          if event_id > low and event_id < high:
            ret.append((event_id, state))
    return ret

  def gc(self):
    for switch_id in sorted(self.log.keys()):
      for link_id in sorted(self.log[switch_id].keys()):
        l = sorted(self.log[switch_id][link_id].keys())
        l.reverse()
        if len(l) > self.gc_param:
          l = l[self.gc_param:]
          for k in l:
            del self.log[switch_id][link_id][k]

  def __str__(self):
    ret = ""
    for switch_id in sorted(self.log.keys()):
      for link_id in sorted(self.log[switch_id].keys()):
        for event_id in sorted(self.log[switch_id][link_id].keys()):
          state = self.log[switch_id][link_id][event_id]
          s = str(switch_id) + '\t' + str(link_id) + '\t' + str(event_id) + '\t' + str(state) + '\n'
          ret += s
    return ret

class LSGossipControl (LSController):
  def __init__ (self, name, ctx, address):
    super(LSGossipControl, self).__init__(name, ctx, address)
    self._hosts = set()
    self._nodes = set()
    self._controllers = set([self.name])
    self.update_messages = {}
    self.reason = None
    self.switch_update_duratiton = ctx.config.controller_switch_info_delay
    self.ctx.schedule_task(self.switch_update_duratiton, lambda: self.periodic_switch_update())
    #self.GetSwitchInformation()
    self.link_version = {}
    self.switch_tables = defaultdict(lambda: defaultdict(lambda: None))

    # Gossip
    self.switchboard[ControlPacket.Gossip] = self.GossipReply
    self.switchboard[ControlPacket.GossipReply] = self.GossipReceive
    self.log = Log(5)
    self.gossip_period = ctx.config.gossip_period
    self.ctx.schedule_task(self.gossip_period, lambda: self.Gossip())
    self.ctx.schedule_task(self.gossip_period, lambda: self.GossipGC())
  
  def periodic_switch_update (self):
    print "%f Requesting switch info %s"%(self.ctx.now, self.name)
    self.GetSwitchInformation()
    self.ctx.schedule_task(self.switch_update_duratiton, lambda: self.periodic_switch_update())

  @property
  def hosts (self):
    return self._hosts

  def PacketIn(self, pkt, src, switch, source, packet):
    pass

  def currentLeader (self, switch):
    for c in sorted(list(self._controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller

  def ComputeNoInstall (self):
    updates = defaultdict(lambda: [])
    #sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    current = 0
    for host in sorted(self._hosts):
      for h2 in sorted(self._hosts):
        if h2 == host:
          continue
        if host.name not in self.graph or h2.name not in self.graph:
          continue
        try:
          paths = list(nx.all_shortest_paths(self.graph, host.name, h2.name))
        except nx.exception.NetworkXNoPath:
          # No path
          continue
        # All of this is just some sort of ploy to get multipathing
        path = paths[current % len(paths)]
        current += 1
        p = SourceDestinationPacket(host.address, h2.address)
        path = zip(path, \
                   path[1:])
        for (a, b) in path[1:]:
          link = self.graph[a][b]['link']
          if self.switch_tables[a][p.pack()] != link:
            updates[a].append((p.pack(), link))
            self.switch_tables[a][p.pack()] = link
    return updates
    #for a in updates.iterkeys():
      ##print "Update to %s with len %d"%(a, len(updates[a]))
      #self.update_messages[self.reason] = self.update_messages.get(self.reason, 0) + 1
      #self.UpdateRules(a, updates[a])

  def ComputeAndUpdatePaths (self):
    #print "Computing paths now"
    #print "%f computing paths"%(self.ctx.now)
    updates = self.ComputeNoInstall()
    #if len(updates) == 0:
      #print "%f no updates"%self.ctx.now
    for a in updates.iterkeys():
      print "%f %s updating %s with len %d"%(self.ctx.now, self.name, a, len(updates[a]))
      print "       Update to %s with len %d"%(a, len(updates[a]))
      self.update_messages[self.reason] = self.update_messages.get(self.reason, 0) + 1
      self.UpdateRules(a, updates[a])

  def GossipReceive(self, pkt, src, s, link_events):
    # s must be in self.log.switches
    for link_id, event_list in link_events.iteritems():
      for e in event_list:
        self.log.add_event(s, link_id, e[0], e[1])

  def GossipReply(self, pkt, src, s, event_list):
    ret = {}
    if s in self.log.get_switches():
      for link_id, el in event_list.iteritems():
        ret[link_id] = []
        for e in el:
          if e == el[0]:
            ret[link_id] = self.log.get_smaller_events(s, link_id, e)
          elif e == el[-1]:
            ret[link_id] = self.log.get_larger_events(s, link_id, e)
          else:
            ret[link_id] = self.log.get_gap_events(s, link_id, e[0], e[1])
    
    pkt_size = 32
    for link_id, el in ret.iteritems():
      pkt_size += 64 + len(el) * (65)

    cpacket = ControlPacket(self.cpkt_id, self.name, src, ControlPacket.GossipReply, [s, ret])
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)

  def GossipHelper(self):
    switches = self.log.get_switches()
    for s in switches:
      event_list = self.log.find_gaps(s)
      cpacket = ControlPacket(self.cpkt_id, self.name, ControlPacket.AllCtrlId, ControlPacket.Gossip, [s, event_list])
      # todo: calculate this number
      pkt_size = 32
      for link_id, el in event_list.iteritems():
        pkt_size += 64 + 64 * 2 + (len(el) - 2) * (65)
      cpacket.size += pkt_size
      self.cpkt_id += 1
      self.sendControlPacket(cpacket)
    #print self.name, " Current log\n"
    #print self.log
   
  def Gossip (self):
    #print "Gossip called", self.gossip_period
    self.GossipHelper()
    self.ctx.schedule_task(self.gossip_period, lambda: self.Gossip())

  def GossipGC(self):
    # GCs the log
    self.log.gc()
    self.ctx.schedule_task(self.gossip_period, lambda: self.GossipGC())

  def SwitchUpNoCompute (self, switch):
    self.NotifySwitchUp(None, None, switch)

  def NotifySwitchUp (self, pkt, src, switch):
    #print "%f %s SUP updating controllers are %s"%(self.ctx.now, self.name, self._controllers)
    # Not sure this is necessary?
    if isinstance(switch, HostTrait) and switch not in self._hosts:
      self._hosts.add(switch)

    self.reason = "NotifySwitchUp"
    if isinstance(switch, ControllerTrait) and switch.name not in self._controllers:
      self._controllers.add(switch.name)
    self._nodes.add(switch)
    self.graph.add_node(switch.name)
    self.reason = None

  def LinkUpNoCompute (self, version, switch, link):
    self.link_version[link] = version
    self.addLink(link)

    self._nodes.add(switch)
    if isinstance(switch, HostTrait):
      self._hosts.add(switch)
    if isinstance(switch, ControllerTrait) and switch.name not in self._controllers:
      self._controllers.add(switch.name)

    self.log.add_event(switch, link, version, True)

  def NotifyLinkUp (self, pkt, src, version, switch, link):
    print "%f %s notify link up %s"%(self.ctx.now, self.name, link), " version: ", version
    if self.link_version.get(link, 0) >= version:
      #print "%f Skipping because of link version"%self.ctx.now
      return # Skip since we already saw this

    components_before = nx.connected_components(self.graph)

    self.LinkUpNoCompute(version, switch, link)

    self.reason = "NotifyLinkUp"
    assert(switch.name in self.graph)

    components_after = nx.connected_components(self.graph)
    assert(switch.name in self.graph)
    
    #print "%f Computing link updates"%self.ctx.now

    self.ComputeAndUpdatePaths()
    if components_before != components_after:
      self.GetSwitchInformation()
    self.reason = None

    # store state in log
    self.log.add_event(switch.name, link, version, True)

  def NotifyLinkDown (self, pkt, src, version, switch, link):
    print "%f %s notify link down %s"%(self.ctx.now, self.name, link), " version: ", version
    if self.link_version.get(link, 0) >= version:
      print "%f Skipping because of link version"%self.ctx.now
      return # Skip since we already saw this
    self.link_version[link] = version
    self.reason = "NotifyLinkDown"
    self.removeLink(link)
    assert(switch.name in self.graph)
    self._nodes.add(switch)
    if isinstance(switch, HostTrait):
      self._hosts.append(switch)
    if isinstance(switch, ControllerTrait) and switch.name not in self._controllers:
      self._controllers.add(switch.name)
    print "%f Computing link updates"%self.ctx.now
    self.ComputeAndUpdatePaths()
    self.reason = None

    # store state in log
    self.log.add_event(switch.name, link, version, False)
    

  def NotifySwitchInformation (self, pkt, src, switch, version_links):
    # Switch information
    self.reason = "NotifySwitchInformation"
    has_changed = False
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)

    filter_links = []
    for (version, link) in version_links:
      if self.link_version.get(link, 0) > version:
        # We have newer information, record that we want to filter this information
        filter_links.append(link)
      else:
        self.link_version[link] = version

    filter_links = set(filter_links)
    version_links = filter(lambda (v, l): l not in filter_links, version_links)

    links = map(lambda (v, l): l, version_links)

    neighbors = map(lambda l: l.a.name if l.b.name == switch.name else l.b.name, links)
    neighbor_to_link = dict(zip(neighbors, links))
    self.graph.add_node(switch.name)
    g_neighbors = self.graph.neighbors(switch.name)
    gn_set = set(g_neighbors)
    n_set = set(neighbors)
    for neighbor in neighbors:
      if neighbor not in gn_set:
        has_changed = True
        self.graph.add_edge(switch.name, neighbor, link=neighbor_to_link[neighbor])
    for neighbor in g_neighbors:
      if neighbor not in n_set:
        has_changed = True
        self.graph.remove_edge(switch.name, neighbor)
    assert(switch.name in self.graph)
    if has_changed:
      self.ComputeAndUpdatePaths()
    self.reason = None
