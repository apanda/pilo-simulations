from env import *
import networkx as nx
class CoordinatingControl (LS2PCController):
  def __init__ (self, name, ctx, addr):
    super(CoordinatingControl, self).__init__(name, ctx, addr)
    self.hosts = set()
    self.controllers = set([self.name])
    self.switches = set()
    self.currently_leader_for = set()
    self.outstanding_request_for_switch = {}

  def PacketIn(self, src, switch, source, packet):
    print "(%s) %s Don't know path, dropping packet from %d to %d"%\
            (self.name, switch.name, packet.source, packet.destination)

  def shouldBeCurrentLeader (self, switch):
    for c in sorted(list(self.controllers)):
      if nx.has_path(self.graph, c, switch):
        return c #Find the first connected controller
    return None
  
  def updateSwitchLeadership (self):
    for switch in self.switches:
      if self.shouldBeCurrentLeader(switch) == self.name and \
              switch not in self.currently_leader_for:
        # Request that we become the leader. In many cases this 
        # will fail
        #print "%f %s asking to be leader for %s"%(self.ctx.now, self.name, switch)
        self.SetSwitchLeadership(switch, self.name)

  def MaybeRequestRelinquishing (self, current_controller, switch):
    """Send a request for current_controller to relinquish control of switch 
      if connect we think it is connected to the switch (and hence to us), otherwise
      just send the switch a request to set leadership"""
    if nx.has_path(self.graph, current_controller, switch):
      # Is connected (and we think we should be leader, so we are also connected to
      # the switch and controller)
      #print "%f %s asking %s to relinquish leadership for %s"%(self.ctx.now, self.name, current_controller, switch)
      cpacket = ControlPacket(self.cpkt_id, \
                              self.name,\
                              current_controller,\
                              ControlPacket.RequestRelinquishLeadership,\
                              [switch, self.name]) 
      self.cpkt_id += 1
      self.sendControlPacket(cpacket)
    else:
      # Is not connected so just ask switch
      self.SetSwitchLeadership(switch, self.name)

  def NotifyAckSetSwitchLeader(self, src, success, current_controller):
    if current_controller == self.name and src not in self.currently_leader_for:
      # Successfully became leader
      print "%f %s is now leader for %s"%(self.ctx.now, self.name, src)
      self.currently_leader_for.add(src)
      self.ComputeAndUpdatePaths() # Update switch as necessary
    elif success and src in self.currently_leader_for:
      #print "%f %s successfully renounced leadership for %s"%(self.ctx.now, self.name, src)
      # Successfully left leadership
      self.currently_leader_for.remove(src)
      # Should we actually still be leader?
      shouldBeLeader = (self.shouldBeCurrentLeader(src) == self.name)
      # Ack any outstanding requests to relinquish leadership
      if src in self.outstanding_request_for_switch:
        dest = self.outstanding_request_for_switch[src]
        del self.outstanding_request_for_switch[src]
        self.ackRequestRelinquish(dest, src, not shouldBeLeader)
      # Retry if we should be leader
      if shouldBeLeader:
        #print "%f %s trying to reacquire leadership for %s"%(self.ctx.now, self.name, src)
        self.SetSwitchLeadership(src, self.name)
    elif not success and \
            self.shouldBeCurrentLeader(src) == self.name and\
            src not in self.currently_leader_for: # We should still be controller
      # Ask current controller to relinquish
      #print "%f %s Should be leader for %s but %s is instead"%(self.ctx.now, self.name, src, current_controller)
      self.MaybeRequestRelinquishing(current_controller, src)

  def ackRequestRelinquish (self, dest, switch, success):
      #print "%f %s acking relinquish for %s (%s) with %s"%(self.ctx.now, self.name, dest, switch, success)
      cpacket = ControlPacket(self.cpkt_id, \
                              self.name,\
                              dest,\
                              ControlPacket.AckRelinquishLeadership,\
                              [switch, success]) 
      self.cpkt_id += 1
      self.sendControlPacket(cpacket)
    
  def NotifyRequestRelinquishLeadership (self, src, switch, other_controller):
    #print "%f %s requested to relinquish leadership for switch %s"%(self.ctx.now, self.name, switch)
    if switch not in self.currently_leader_for:
      #print "%f %s is not leader for requested switch %s"%(self.ctx.now, self.name, switch)
      self.ackRequestRelinquish(src, switch, False)
    elif self.shouldBeCurrentLeader(switch) == self.name:
      #print "%f %s ctrlr %s asked for leadership of %s but state says no (controllers are %s)"%(self.ctx.now, self.name, \
              #src, switch, sorted(self.controllers))
      # Am leader, should be leader, don't give up
      self.ackRequestRelinquish(src, switch, False)
    else:
      #print "%f %s ctrlr %s asked for leadership of %s and state says yes"%(self.ctx.now, self.name, src, switch)
      # Am leader, should not be leader, let the other person take over
      if switch in self.outstanding_request_for_switch and \
              self.outstanding_request_for_switch[switch] != src:
        # Only one of these should win, blindly let newer request win
        #print "%f %s ctrlr %s previously asked for leadership of %s and but is kicked out by %s"%(self.ctx.now,\
                #self.name,\
                #self.outstanding_request_for_switch[switch],
                #switch,\
                #src)
        self.ackRequestRelinquish(self.outstanding_request_for_switch[switch], switch, False)
        self.outstanding_request_for_switch[switch] = src
      else:
        # No one has requested yet, send a request
        self.outstanding_request_for_switch[switch] = src
        self.SetSwitchLeadership(switch, "")

  def NotifyAckRelinquishLeadership (self, src, switch, success):
    if success or switch in self.currently_leader_for:
      #print "%f %s Ctrlr %s relinquished leadership of %s"%(self.ctx.now, self.name, src, switch)
      # Woohoo, they relinquished, let us ask for leadership
      self.SetSwitchLeadership(switch, self.name)
    elif self.shouldBeCurrentLeader(switch) == self.name and switch not in self.currently_leader_for:
      #print "%f %s Ctrlr %s did not relinquish leadership of %s but we should be leader"%(self.ctx.now, self.name, src, switch)
      # Failed, but we should still be leader. Might have failed since
      # the old leader is no longer the leader, so start from the beginning
      self.SetSwitchLeadership(switch, self.name)
    #else:
      #print "%f %s Ctrlr %s did not relinquish leadership of %s but we should not be leader"%(self.ctx.now, self.name, src, switch)

  def ComputeAndUpdatePaths (self):
    sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
    #print "%f Shortest paths are "%(self.ctx.now)
    #print sp
    #print "%f hosts are %s"%(self.ctx.now ,self.hosts)
    for host in self.hosts:
      for h2 in self.hosts:
        if h2 == host:
          continue
        if h2.name in sp[host.name]:
          p = SourceDestinationPacket(host.address, h2.address)
          path = zip(sp[host.name][h2.name], \
                    sp[host.name][h2.name][1:])
          for (a, b) in path[1:]:
            #if 'switch' not in self.graph.node[a]:
              #continue      
            #ao = self.graph.node[a]['switch']
            link = self.graph[a][b]['link']
            if a in self.currently_leader_for:
              #print "%f %s leader for %s controllers are %s"%(self.ctx.now, self.name, a, self.controllers)
              self.UpdateRules(a, [(p.pack(), link)])
    self.updateSwitchLeadership()
  
  def maintainSets(self, switch):
    if isinstance(switch, ControllerTrait):
      self.controllers.add(switch.name)
    elif isinstance(switch, HostTrait):
      self.hosts.add(switch)
    else:
      self.switches.add(switch.name)

  def NotifySwitchUp (self, src, switch):
    #print "%f Heard about switch %s"%(self.ctx.now, switch.name)
    # Not sure this is necessary?
    self.graph.add_node(switch.name, switch = switch)
    self.maintainSets(switch)
    self.ComputeAndUpdatePaths()
    #self.graph[switch.name]['obj'] = switch

  def NotifyLinkUp (self, src, switch, link):
    #print "%f Heard about link %s"%(self.ctx.now, link)
    self.graph.add_edge(link.a.name, link.b.name, link=link)
    assert(switch.name in self.graph)
    self.maintainSets(switch)
    self.ComputeAndUpdatePaths()
    if link.a.name == self.name or link.b.name == self.name:
      # Something changed for us, find out (essentially we know for sure
      # we need to query information). Actually we should probably query all
      # the time when a link comes up (stuff has changed)
      self.GetSwitchInformation()

  def NotifyLinkDown (self, src, switch, link):
    #print "%f Heard about link down %s"%(self.ctx.now, link)
    if self.graph.has_edge(link.a.name, link.b.name):
      self.graph.remove_edge(link.a.name, link.b.name)
    assert(switch.name in self.graph)
    self.maintainSets(switch)
    self.ComputeAndUpdatePaths()

  def NotifySwitchInformation (self, src, switch, links):
    self.maintainSets(switch)
    neighbors = map(lambda l: l.a.name if l.b.name == switch.name else l.b.name, links)
    neighbor_to_link = dict(zip(neighbors, links))
    self.graph.add_node(switch.name)
    g_neighbors = self.graph.neighbors(switch.name)
    gn_set = set(g_neighbors)
    n_set = set(neighbors)
    for neighbor in neighbors:
      if neighbor not in gn_set:
        self.graph.add_edge(switch.name, neighbor, link=neighbor_to_link[neighbor])
    for neighbor in g_neighbors:
      if neighbor not in n_set:
        self.graph.remove_edge(switch.name, neighbor)
    assert(switch.name in self.graph)
    self.ComputeAndUpdatePaths()

def Main():
  ctx = Context()
  ctrl0 = CoordinatingControl('c1', ctx, 10)
  ctrl1 = CoordinatingControl('c2', ctx, 11)
  switches = [LS2PCSwitch('s%d'%(i), ctx) for i in xrange(1, 4)]
  host_a = Host('a', ctx, 1)
  host_b = Host('b', ctx, 2)
  host_c = Host('c', ctx, 3)
  hosts = [host_a, host_b, host_c]
  links = [Link(ctx, host_a, switches[0]), \
           Link(ctx, host_b, switches[1]), \
           Link(ctx, host_c, switches[2]), \
           Link(ctx, switches[0], switches[1]), \
           Link(ctx, ctrl1, switches[1]), \
           Link(ctx, switches[1], switches[2]), \
           Link(ctx, switches[0], switches[2])]

  for link in links:
    ctx.schedule_task(0, link.SetUp)

  linkLowCtrl = Link(ctx, ctrl0, switches[0])
  ctx.schedule_task(100, linkLowCtrl.SetUp)
  print "Starting"
  p = SourceDestinationPacket(1, 3)
  ctx.schedule_task(800, lambda: host_a.Send(p))
  p2 = SourceDestinationPacket(2, 3)
  ctx.schedule_task(800, lambda: host_a.Send(p2))
  p3 = FloodPacket("Hello")
  ctx.schedule_task(800, lambda: host_a.Send(p3))
  ctx.final_time = 8000
  ctx.run()
if __name__ == "__main__":
  Main()
