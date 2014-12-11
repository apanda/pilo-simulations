from env import *
import networkx as nx
class LSGossipControl (LSController):
  def __init__ (self, name, ctx, address):
    super(LSGossipControl, self).__init__(name, ctx, address)
    self._hosts = set()
    self._nodes = set()
    self._controllers = set([self.name])
    self.announcements = set()
    #self.connected_to_node = {self.name: True}
    self.update_messages = {}
    self.reason = None
  
  @property
  def hosts (self):
    return self._hosts

  def PacketIn(self, pkt, src, switch, source, packet):
    pass

  def currentLeader (self, switch):
    #print "%f %s controllers are %s"%(self.ctx.now, self.name, self._controllers)
    for c in sorted(list(self._controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller

  def ComputeAndUpdatePaths (self):
    #print "%f %s compute and update paths"%(self.ctx.now, self.name)
    #print "%f %s hosts are %s"%(self.ctx.now, self. name, self._hosts)
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    for host in self._hosts:
      #print "%f %s connectivity %s %s"%(self.ctx.now, self. name, host.name, sp[host.name])
      for h2 in self._hosts:
        if h2 == host:
          continue
        if h2.name in sp[host.name]:
          p = SourceDestinationPacket(host.address, h2.address)
          path = zip(sp[host.name][h2.name], \
                    sp[host.name][h2.name][1:])
          for (a, b) in path[1:]:
            link = self.graph[a][b]['link']
            self.update_messages[self.reason] = self.update_messages.get(self.reason, 0) + 1
            self.UpdateRules(a, [(p.pack(), link)])
  
  def Gossip (self):
    pass
  
  def NotifySwitchUp (self, pkt, src, switch):
    #print "%f %s SUP updating controllers are %s"%(self.ctx.now, self.name, self._controllers)
    self.announcements.add((pkt.id, ControlPacket.NotifySwitchUp, src, switch))
    # Not sure this is necessary?
    if isinstance(switch, HostTrait) and switch not in self._hosts:
      self._hosts.add(switch)

    self.reason = "NotifySwitchUp"
    if isinstance(switch, ControllerTrait) and swith.name not in self._controllers:
      self._controllers.add(switch.name)
      #print "%f %s learnt new controller, controllers are %s"%(self.ctx.now, self.name, self._controllers)
      self.connected_to_node[switch.name] = False

    self.ComputeAndUpdatePaths()

    if switch not in self._nodes:
      self.GetSwitchInformation()
    self._nodes.add(switch)
    self.reason = None

  def NotifyLinkUp (self, pkt, src, switch, link):
    self.reason = "NotifyLinkUp"
    components_before = nx.connected_components(self.graph)
    self.addLink(link)
    components_after = nx.connected_components(self.graph)
    self.announcements.add((pkt.id, ControlPacket.NotifyLinkUp, src, switch, link))
    assert(switch.name in self.graph)
    self._nodes.add(switch)
    if isinstance(switch, HostTrait):
      self._hosts.add(switch)
    if isinstance(switch, ControllerTrait) and switch.name not in self._controllers:
      self._controllers.add(switch.name)
      #print "%f %s learnt new controller, controllers are %s"%(self.ctx.now, self.name, self._controllers)
    self.ComputeAndUpdatePaths()
    if components_before != components_after:
      self.GetSwitchInformation()
    self.reason = None

  def NotifyLinkDown (self, pkt, src, switch, link):
    self.reason = "NotifyLinkDown"
    self.removeLink(link)
    self.announcements.add((pkt.id, ControlPacket.NotifyLinkDown, src, switch, link))
    assert(switch.name in self.graph)
    self._nodes.add(switch)
    if isinstance(switch, HostTrait):
      self._hosts.append(switch)
    if isinstance(switch, ControllerTrait) and switch.name not in self._controllers:
      self._controllers.add(switch.name)
      #print "%f %s learnt new controller, controllers are %s"%(self.ctx.now, self.name, self._controllers)
    self.ComputeAndUpdatePaths()
    self.reason = None

  def NotifySwitchInformation (self, pkt, src, switch, links):
    self.reason = "NotifySwitchInformation"
    has_changed = False
    if isinstance(switch, HostTrait):
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
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
