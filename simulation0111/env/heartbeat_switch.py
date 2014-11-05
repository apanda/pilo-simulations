from . import Context, HeartbeatPacket, Link, Switch, ControlPacket, SourceDestinationPacket
import networkx as nx
class HBSwitch (Switch):
  """A switch that sends and receives periodic heartbeats from
  other network elements. Epoch is time when previously received
  heartbeats expire, while send rate is the rate at which these things
  are sent. This is equivalent to Layer 0 (Layer A) for the heartbeat case"""
  def __init__ (self, name, ctx, epoch, send_rate):
    super(HBSwitch, self).__init__(name, ctx)
    self.epoch = epoch
    self.send_rate = send_rate
    self.receivedBeats = {}
    self.connectivityMatrix = {}
    self.ctx.schedule_task(self.send_rate, self.sendHeartbeat)
    self.controllers = set()

  @property
  def probableLeader (self):
    connectivity_measure = sorted(map(lambda c: (-1 * len(self.connectivityMatrix.get(c, [])), c), self.controllers))
    if len(connectivity_measure) > 0 and \
       connectivity_measure[0][0] != 0: # Things are connected, etc.
      return connectivity_measure[0][1]
    return None

  def updateAndCullHeartbeats (self):
    """Remove heartbeats as appropriate"""
    to_remove = []
    for (src, hb) in self.receivedBeats.iteritems():
      if hb + self.epoch < self.ctx.now:
        to_remove.append(src)
    for src in to_remove:
      del self.receivedBeats[src]
      del self.connectivityMatrix[src]
    self.connectivityMatrix[self.name] = sorted(list(self.receivedBeats.keys()))

  def sendHeartbeat (self):
    #print "%f %s sending heartbeat"%(self.ctx.now, self.name)
    self.updateAndCullHeartbeats()
    p = HeartbeatPacket(self.cpkt_id, \
            self.name, \
            list(self.links), \
            sorted(list(self.receivedBeats.keys())), \
            self)
    self.cpkt_id += 1
    self.Flood(None, p)
    self.ctx.schedule_task(self.send_rate, self.sendHeartbeat)
  
  def receive (self, link, source, packet):
    if isinstance(packet, HeartbeatPacket):
      self.processHeartbeat(packet)
    super(HBSwitch, self).receive(link, source, packet)

  def processHeartbeat(self, hbpacket):
    #print "%f %s received heartbeat from %s"%(self.ctx.now, self.name, hbpacket.src)
    # Update the heartbeat messages
    self.receivedBeats[hbpacket.src] = self.ctx.now
    # Update connectivity matrix
    self.connectivityMatrix[hbpacket.src] = hbpacket.heard_from
    if isinstance(hbpacket.sobj, HBController):
      self.controllers.add(hbpacket.src)
    # Don't use link state information
    self.UpdatedConnectivity()

  def UpdatedConnectivity(self):
    pass

  def updateRules (self, source, match_action_pairs):
    if self.probableLeader != source:
      print "%f %s  updated by %s (I think leader should be %s)"%(self.ctx.now, self.name, source, self.probableLeader)
    super(HBSwitch, self).updateRules(source, match_action_pairs)
  

class HBHost (HBSwitch):
  def __init__ (self, name, ctx, address, epoch, send_rate):
    super(HBHost, self).__init__(name, ctx, epoch, send_rate)
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

class HBController (HBHost):
  """Base class for controllers"""
  def __init__ (self, name, ctx, address, epoch, send_rate):
    super(HBController, self).__init__(name, ctx, address, epoch, send_rate)
    self.switchboard = {
     ControlPacket.NotifySwitchUp: self.NotifySwitchUp,
     ControlPacket.NotifyLinkDown: self.NotifyLinkDown,
     ControlPacket.NotifyLinkUp: self.NotifyLinkUp,
     ControlPacket.PacketIn: self.PacketIn,
     ControlPacket.SwitchInformation: self.NotifySwitchInformation,
     ControlPacket.GetSwitchInformation: self.processSwitchInformation
    }
    self.cpkt_id = 0
  def receive (self, link, source, packet):
    if isinstance(packet, ControlPacket):
      # Received a control packet
      if packet.dest_id == ControlPacket.AllCtrlId or packet.dest_id == self.name:
        #print "%s received a control packet type %d"%(self.name, packet.message_type)
        if packet.message_type in self.switchboard:
          delay = self.ctx.config.ControlLatency
          self.ctx.schedule_task(delay, lambda: self.switchboard[packet.message_type](packet.src_id, *packet.message))
        else:
          self.UnknownPacket(source, packet)
    elif isinstance(packet, HeartbeatPacket):
      self.processHeartbeat(packet)

  def sendControlPacket(self, packet):
    delay = self.ctx.config.ControlLatency
    self.ctx.schedule_task(delay, lambda: self.Send(packet))
  def ForwardPacket (self, switch, link, packet):
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.ForwardPacket, [link, packet]) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)
  def UpdateRules (self, switch, pairs):
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.UpdateRules, [pairs]) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)
  def GetSwitchInformation (self):
    cpacket = ControlPacket(self.cpkt_id, self.name, ControlPacket.AllCtrlId, ControlPacket.GetSwitchInformation, []) 
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)
  def NotifySwitchUp (self, source, switch):
    raise NotImplementedError
  def NotifyLinkDown (self, source, switch, link):
    raise NotImplementedError
  def NotifyLinkUp (self, source, switch, link):
    raise NotImplementedError
  def NotifySwitchInformation (self, source, switch, links):
    raise NotImplementedError
  def PacketIn(self, src, switch, source, packet):
    raise NotImplementedError
  def UnknownPacket(self, src, packet):
    print "%s unknown message type %d"%(self.name, packet.message_type) 
  def UpdatedConnectivity (self):
    raise NotImplementedError
