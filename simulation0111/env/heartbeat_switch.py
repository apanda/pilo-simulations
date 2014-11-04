from . import Context, HeartbeatPacket, Link, LeaderComputingSwitch, ControlPacket
import networkx as nx
class HBSwitch (LeaderComputingSwitch):
  """A switch that sends and receives periodic heartbeats from
  other network elements. Epoch is time when previously received
  heartbeats expire, while send rate is the rate at which these things
  are sent"""
  def __init__ (self, name, ctx, epoch, send_rate):
    super(HBSwitch, self).__init__(name, ctx)
    self.controllers = set()
    self.epoch = epoch
    self.send_rate = send_rate
    self.receivedBeats = {}
    self.connectivityMatrix = {}
    self.ctx.schedule_task(self.send_rate, self.sendHeartbeat)
    self.leader = None

  @property
  def currentLeader(self):
    return self.leader

  def updateAndCullHeartbeats (self):
    """Remove heartbeats as appropriate"""
    to_remove = []
    for (src, hb) in self.receivedBeats.iteritems():
      if hb + self.epoch < self.ctx.now:
        to_remove.append(src)
    for src in to_remove:
      del self.receivedBeats[src]
      del self.connectivityMatrix[src]

  def sendHearbeat (self):
    self.updateAndCullHeartbeats()
    p = HeartbeatPacket(self.name, \
            list(self.links), \
            sorted(list(self.receivedBeats.keys())))
    self.Flood(None, p)
    self.ctx.schedule_task(self.send_rate, self.sendHeartbeat)
  
  def receive (self, link, source, packet):
    if isinstance(packet, HeartbeatPacket):
      self.processHeartbeat(packet)
    super(HBSwitch, self).receive(link, source, packet)

  def processHeartbeat(self, hbpacket):
    # Update the heartbeat messages
    self.receivedBeats[hbpacket.src] = self.ctx.now
    # Update connectivity matrix
    self.connectivityMatrix[hbpacket.src] = hbpacket.heard_from
    # Update graph
    neighbors = map(lambda l: l.a.name if l.b.name == hbpacket.src else l.b.name, \
                    hbpacket.direct_links)
    g_neighbors = self.g.neighbors(hbpacket.src)
    gn_set = set(g_neighbors)
    n_set = set(neighbors)
    for neighbor in neighbors:
      if neighbor not in gn_set:
        self.g.add_edge(switch.name, neighbor)
    for neighbor in g_neighbors:
      if neighbor not in n_set:
        self.g.remove_edge(switch.name, neighbor)

  def UpdatedConnectivityAndGraph(self):
    """Deal with the fact that things have been updated. Currently
      just appoint the most connected, lowest ID controller leader"""
    connectivity_measure = sorted(map(lambda c: (len(self.connectivityMatrix.get(c, [])), c), self.controllers), \
                                  reverse = True)
    if len(connectivity_measure) > 0 and connectivity_measure[0][0] != 0: # Things are connected, etc.
      print "%f %s Setting %s as leader"%(self.ctx.now, self.name, self.currentLeader)
      self.leader = self.connectivity_measure[0][1]
  

class HBHost (HBSwitch):
  def __init__ (self, name, ctx, address):
    super(HBHost, self).__init__(name, ctx)
    self.address = address

  def receive (self, link, source, packet):
    if isinstance(packet, SourceDestinationPacket):
      print "%f %s Received from %d to %d"%(self.ctx.now, self.name, packet.source, packet.destination)
    elif isinstance(packet, ControlPacket):
      self.processControlMessage (link, source, packet)
    elif isinstance(packet, HeartbeatPacket):
      self.processHeartbeat(packet)

  def Send (self, packet):
    super(HBHost, self).Flood(None, packet)

