from env import *
import networkx as nx
class LSLeaderControl (LSController):
  NACK_DELAY = 100.0 # Wait for a bit before trying things again.
  def __init__ (self, name, ctx, address):
    super(LSLeaderControl, self).__init__(name, ctx, address)
    self.hosts = set()
    self.controllers = set([self.name])
    self._nodes = set()
    self.update_messages = {}
    self.reason = None
    self.GetSwitchInformation()
    self.link_version = {}

  def PacketIn(self, pkt, src, switch, source, packet):
    pass

  def currentLeader (self, switch):
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller

  def ComputeAndUpdatePaths (self):
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    for host in self.hosts:
      for h2 in self.hosts:
        if h2 == host:
          continue
        if h2.name in sp[host.name]:
          p = SourceDestinationPacket(host.address, h2.address)
          path = zip(sp[host.name][h2.name], \
                    sp[host.name][h2.name][1:])
          for (a, b) in path[1:]:
            link = self.graph[a][b]['link']
            if self.currentLeader(a) == self.name:
              self.update_messages[self.reason] = self.update_messages.get(self.reason, 0) + 1
              self.UpdateRules(a, [(p.pack(), link)])

  def NotifySwitchUp (self, pkt, src, switch):
    # Not sure this is necessary?
    should_ask = (switch not in self._nodes)
    self._nodes.add(switch)
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    self.reason = "NotifySwitchUp"
    #self.ComputeAndUpdatePaths()
    #if should_ask:
      #self.GetSwitchInformation()
    self.reason = None

  def NotifyLinkUp (self, pkt, version, src, switch, link):
    if self.link_version.get(link, 0) >= version:
      return # Skip since we already saw this
    self.link_version[link] = version
    components_before = nx.connected_components(self.graph)
    self.addLink(link)
    components_after = nx.connected_components(self.graph)
    assert(switch.name in self.graph)
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    self.reason = "NotifyLinkUp"
    self.ComputeAndUpdatePaths()
    #if link.a.name == self.name or link.b.name == self.name:
      # Something changed for us, find out (essentially we know for sure
      # we need to query information). Actually we should probably query all
      # the time when a link comes up (stuff has changed)
    if components_before != components_after:
      self.GetSwitchInformation()
    self.reason = None

  def NotifyLinkDown (self, pkt, version, src, switch, link):
    if self.link_version.get(link, 0) >= version:
      return # Skip since we already saw this
    self.link_version[link] = version

    self.removeLink(link)
    assert(switch.name in self.graph)
    if isinstance(switch, HostTrait):
      self.hosts.append(switch)
    self.reason = "NotifyLinkDown"
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    self.ComputeAndUpdatePaths()
    self.reason = None

  def NotifySwitchInformation (self, pkt, src, switch, version_links):
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
    self.reason = "NotifySwitchInformation"
    if has_changed:
      self.ComputeAndUpdatePaths()
    self.reason = None

  def NotifyNackUpdate (self, packet, src):
    def NotifyNackInternal ():
      if self.currentLeader(src) == self.name:
      # The update was not accepted, but this controller should still be leader. Let us try updating again.
        self.ComputeAndUpdatePaths()
    self.ctx.schedule_task(LSLeaderControl.NACK_DELAY, NotifyNackInternal)
