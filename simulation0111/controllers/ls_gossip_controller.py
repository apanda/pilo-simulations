from env import *
import networkx as nx
class LSGossipControl (LSController):
  def __init__ (self, name, ctx, address):
    super(LSGossipControl, self).__init__(name, ctx, address)
    self._hosts = set()
    self._controllers = set([self.name])
    self.announcements = set()
    self.connected_to_controller = {self.name: True}

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
            if self.currentLeader(a) == self.name:
              #print "%f %s updating %s (%s - %s), leader %s"% \
                   #(self.ctx.now, self.name, a, host.name, \
                            #h2.name, self.currentLeader(a))
              self.UpdateRules(a, [(p.pack(), link)])
            #else:
              #print "%f %s not updating %s (%s - %s), not leader (ldr %s)"% \
                   #(self.ctx.now, self.name, a, host.name, \
                            #h2.name, self.currentLeader(a))
  
  def Gossip (self):
    announcements = list(self.announcements)
    self.sendToController(ControlPacket.SwitchInformation, \
                          [announcements])
  
  def controllerConnectivityChanged (self):
    should_gossip = False
    #print "%f %s controller connectivity before %s"%(self.ctx.now, self.name, self.connected_to_controller)
    for k in self._controllers:
      connectivity = nx.has_path(self.graph, self.name, k)
      if (not self.connected_to_controller.get(k, False)) and \
            connectivity != self.connected_to_controller.get(k, False):
        should_gossip = True
      self.connected_to_controller[k] = connectivity
    return should_gossip

  def NotifySwitchUp (self, pkt, src, switch):
    #print "%f %s SUP updating controllers are %s"%(self.ctx.now, self.name, self._controllers)
    should_gossip = False
    self.announcements.add((pkt.id, ControlPacket.NotifySwitchUp, src, switch))
    # Not sure this is necessary?
    if isinstance(switch, HostTrait) and switch not in self._hosts:
      self._hosts.add(switch)

    if isinstance(switch, ControllerTrait) and swith.name not in self._controllers:
      self._controllers.add(switch.name)
      #print "%f %s learnt new controller, controllers are %s"%(self.ctx.now, self.name, self._controllers)
      self.connected_to_controller[switch.name] = False
      should_gossip = True

    if self.controllerConnectivityChanged():
      should_gossip = True
    self.ComputeAndUpdatePaths()

    if should_gossip:
      self.Gossip()

  def NotifyLinkUp (self, pkt, src, switch, link):
    #print "%f %s LUP %s updating controllers are %s"%(self.ctx.now, link, self.name, self._controllers)
    should_gossip = False
    key = (pkt.id, ControlPacket.NotifyLinkUp, src, switch, link)
    if key not in self.announcements:
      #print "%f %s updating, unknown notification %s"%(self.ctx.now, self.name, key)
      # This is new
      self.addLink(link)
      self.announcements.add((pkt.id, ControlPacket.NotifyLinkUp, src, switch, link))
      assert(switch.name in self.graph)
      if isinstance(switch, HostTrait):
        self._hosts.add(switch)
      if isinstance(switch, ControllerTrait) and switch.name not in self._controllers:
        self._controllers.add(switch.name)
        #print "%f %s learnt new controller, controllers are %s"%(self.ctx.now, self.name, self._controllers)
        should_gossip = True
      if self.controllerConnectivityChanged():
        should_gossip = True
      self.ComputeAndUpdatePaths()
      if should_gossip:
        self.Gossip() # Gossip whenever things change

  def NotifyLinkDown (self, pkt, src, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    #print "%f %s LDN %s updating controllers are %s"%(self.ctx.now, link, self.name, self._controllers)
    should_gossip = False
    key = (pkt.id, ControlPacket.NotifyLinkDown, src, switch, link)
    if  key not in self.announcements:
      #print "%f %s updating, unknown notification %s"%(self.ctx.now, self.name, key)
      # This is new
      self.removeLink(link)
      self.announcements.add((pkt.id, ControlPacket.NotifyLinkDown, src, switch, link))
      assert(switch.name in self.graph)
      if isinstance(switch, HostTrait):
        self._hosts.append(switch)
      if isinstance(switch, ControllerTrait) and switch.name not in self._controllers:
        self._controllers.add(switch.name)
        #print "%f %s learnt new controller, controllers are %s"%(self.ctx.now, self.name, self._controllers)
        should_gossip = True
      if self.controllerConnectivityChanged():
        should_gossip = True
      self.ComputeAndUpdatePaths()
      if should_gossip:
        self.Gossip() # Gossip whenever things change

  def NotifySwitchInformation (self, pkt, src, announcements):
    #print "%f %s updating GOS controllers are %s"%(self.ctx.now, self.name, self._controllers)
    for announcement in announcements:
      if announcement not in self.announcements:
        self.announcements.add(announcement) # Add the current set of announcements.
    should_gossip = False
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
        #print "%f %s applying change from %s id %s"%(self.ctx.now, self.name, s, a[0])
        if a[1] == ControlPacket.NotifyLinkDown:
          change = True
          if isinstance(a[2], ControllerTrait) and a[2].name not in self._controllers:
            #print "%f %s learnt new controller from gossip, controllers are %s"%(self.ctx.now, self.name, self._controllers)
            self._controllers.add(a[2].name)
            should_gossip = True
          if isinstance(a[2], HostTrait):
            self._hosts.add(a[2])
          self.removeLink(a[-1])
        elif a[1] == ControlPacket.NotifyLinkUp:
          change = True
          if isinstance(a[2], ControllerTrait) and a[2].name not in self._controllers:
            #print "%f %s learnt new controller from gossip, controllers are %s"%(self.ctx.now, self.name, self._controllers)
            self._controllers.add(a[2].name)
            should_gossip = True
          if isinstance(a[2], HostTrait):
            self._hosts.add(a[2])
          self.addLink(a[-1])
        elif a[1] == ControlPacket.NotifySwitchUp:
          change = True
          if isinstance(a[2], ControllerTrait) and a[2].name not in self._controllers:
            #print "%f %s learnt new controller from gossip, controllers are %s"%(self.ctx.now, self.name, self._controllers)
            self._controllers.add(a[2].name)
            should_gossip = True
          if isinstance(a[2], HostTrait):
            self._hosts.add(a[2])
          self.addLink(a[-1])
        # Ignore switch ups
    if change:
      self.ComputeAndUpdatePaths()
      if self.controllerConnectivityChanged():
        should_gossip = True
      if should_gossip:
        self.Gossip() # Gossip whenever things change
