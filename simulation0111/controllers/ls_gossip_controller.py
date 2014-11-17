from env import *
import networkx as nx
class LSGossipControl (LSController):
  def __init__ (self, name, ctx, address):
    super(LSGossipControl, self).__init__(name, ctx, address)
    self.hosts = set()
    self.controllers = set([self.name])
    self.announcements = set()
    self.connected_to_controller = {self.name: True}

  def PacketIn(self, pkt, src, switch, source, packet):
    print "(%s) %s Don't know path, dropping packet from %d to %d"%\
            (self.name, switch.name, packet.source, packet.destination)

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
              self.UpdateRules(a, [(p.pack(), link)])
  
  def Gossip (self):
    print "%f %s gossiping"%(self.ctx.now, self.name)
    announcements = list(self.announcements)
    self.sendToController(ControlPacket.SwitchInformation, \
                          [announcements])
  
  def controllerConnectivityChanged (self):
    should_gossip = False
    for k in self.connected_to_controller.keys():
      connectivity = nx.has_path(self.graph, self.name, k)
      if (not self.connected_to_controller[k]) and \
            connectivity != self.connected_to_controller[k]:
        should_gossip = True
      self.connected_to_controller[k] = connectivity
    return should_gossip

  def NotifySwitchUp (self, pkt, src, switch):
    should_gossip = False
    self.announcements.add((pkt.id, ControlPacket.NotifySwitchUp, src, switch))
    # Not sure this is necessary?
    if isinstance(switch, HostTrait) and switch not in self.hosts:
      self.hosts.add(switch)
    if isinstance(switch, ControllerTrait) and swith not in self.controllers:
      self.controllers.add(switch.name)
      self.connected_to_controller[switch.name] = False
      should_gossip = True
    if self.controllerConnectivityChanged():
      should_gossip = True
    self.ComputeAndUpdatePaths()
    if should_gossip:
      self.Gossip()

  def NotifyLinkUp (self, pkt, src, switch, link):
    #print "%f Heard about link %s"%(self.ctx.now, link)
    # Can no longer depend on the underlying graph maintenance alone.
    should_gossip = False
    if (pkt.id, ControlPacket.NotifyLinkUp, src, switch, link) not in self.announcements:
      # This is new
      self.addLink(link)
      self.announcements.add((pkt.id, ControlPacket.NotifyLinkUp, src, switch, link))
      assert(switch.name in self.graph)
      if isinstance(switch, HostTrait):
        self.hosts.add(switch)
      if isinstance(switch, ControllerTrait) and switch not in self.controllers:
        self.controllers.add(switch.name)
        should_gossip = True
      if self.controllerConnectivityChanged():
        should_gossip = True
      self.ComputeAndUpdatePaths()
      if should_gossip:
        self.Gossip() # Gossip whenever things change

  def NotifyLinkDown (self, pkt, src, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    should_gossip = False
    if (pkt.id, ControlPacket.NotifyLinkDown, src, switch, link) not in self.announcements:
      # This is new
      self.removeLink(link)
      self.announcements.add((pkt.id, ControlPacket.NotifyLinkDown, src, switch, link))
      assert(switch.name in self.graph)
      if isinstance(switch, HostTrait):
        self.hosts.append(switch)
      if isinstance(switch, ControllerTrait) and switch not in self.controllers:
        self.controllers.add(switch.name)
        should_gossip = True
      if self.controllerConnectivityChanged():
        should_gossip = True
      self.ComputeAndUpdatePaths()
      if should_gossip:
        self.Gossip() # Gossip whenever things change

  def NotifySwitchInformation (self, pkt, src, announcements):
    for announcement in announcements:
      if announcement not in self.announcements:
        self.announcements.add(announcement) # Add the current set of announcements.
    # Sort all of the announcements by source
    srces = set(map(lambda a: a[2], list(self.announcements)))
    announce_dict = {src: [] for src in srces}
    for a in list(self.announcements):
      announce_dict[a[2]].append(a)
    for s in srces:
      announce_dict[s].sort()
    self.graph.clear()
    change = False
    for s in srces:
      for a in announce_dict[s]:
        if a[1] == ControlPacket.NotifyLinkDown:
          change = True
          self.removeLink(a[-1])
        elif a[1] == ControlPacket.NotifyLinkUp:
          change = True
          self.addLink(a[-1])
        elif a[1] == ControlPacket.NotifySwitchUp:
          change = True
          self.addLink(a[-1])
        # Ignore switch ups
    if change:
      self.ComputeAndUpdatePaths()
