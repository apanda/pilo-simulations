from . import Switch, Controller, ControlPacket, FloodPacket, SourceDestinationPacket, MarkedSourceDestPacket, Host, EncapSourceDestPacket

import random

def WaypointSwitchClass(base):
  class WaypointSwitch(base):
    def __init__(self, *args):
      super(WaypointSwitch, self).__init__(*args)
      self.waypoint_rules = {
        "SRC": {},
        "DEST": {}
      }
      self.ctrl_switchboard[ControlPacket.UpdateWaypointRules] = self.updateWaypointRules
      self.is_middlebox = False
    
    def receive(self, link, source, packet):
      if isinstance(packet, MarkedSourceDestPacket):
        print self, " received ", packet.mark, "<", packet.source, ",", packet.destination, ">"
        if self.is_middlebox and \
           (packet.source in self.waypoint_rules["SRC"] \
            or packet.destination in self.waypoint_rules["DEST"]):
          print self, "processing unmarked packet ", "<", packet.source, ",", packet.destination, ">"
          packet.set_mark()
      super(WaypointSwitch, self).receive(link, source, packet)
      
    def processControlMessage (self, link, source, packet):
      if packet.message_type == ControlPacket.UpdateWaypointRules:
        delay = self.ctx.config.UpdateDelay
        self.ctx.schedule_task(delay, lambda: self.updateWaypointRules(packet.message))
        return True
      return super(WaypointSwitch, self).processControlMessage(link, source, packet)

    def updateWaypointRules (self, new_rules):
      self.waypoint_rules = {"SRC": set(), "DEST": set()}
      self.is_middlebox = False
      for host in new_rules.keys():
        (s_wp, d_wp) = new_rules[host]
        if s_wp == self.name:
          self.is_middlebox = True
          self.waypoint_rules["SRC"].add(host.address)
        if d_wp == self.name:
          self.is_middlebox = True
          self.waypoint_rules["DEST"].add(host.address)

  return WaypointSwitch


def WaypointHostClass(base):
  class WaypointHost(base):
    def __init__ (self, *args):
      super(WaypointHost, self).__init__(*args)

    def receive (self, link, source, packet):
      if isinstance(packet, MarkedSourceDestPacket):
        if packet.mark == True:
          print self, " received marked pkt from ", packet.source

      super(WaypointHost, self).receive(link, source, packet)
  return WaypointHost(base)
    
class LoadBalancingSwitch(object):
  ENCAP = 1
  TRANSIT = 2
  DECAP = 3
  NO_ROLE = 4
  def __init__(self):
    self.role = LoadBalancingSwitch.NO_ROLE
    self.lb_rules = set([])

  def receive(self, link, source, packet):
    if isinstance(packet, SourceDestinationPacket):
      return self.receiveSD(link, source, packet)
    return packet

  def weighted_choice(self, choices):
    total = sum(choices)
    r = random.uniform(0, total)
    upto = 0
    for idx in range(len(choices)):
      w = choices[idx]
      if upto + w > r:
        return idx
      upto += w
    assert False, "Shouldn't get here"

  def receiveSD(self, link, source, packet):
    if self.role == LoadBalancingSwitch.ENCAP:
      tunnel_id = 0
      test_pkt = EncapSourceDestPacket(tunnel_id, packet)
      if test_pkt.info() in self.rules:
        # need to forward this packet based on the rules
        tunnel_id = self.weighted_choice(self.rules[test_pkt.info()])
        ret_pkt = EncapSourceDestPacket(tunnel_id+1, packet)
        print self, "forwarding", self.rules[test_pkt.info()]
        return ret_pkt
      else:
        return packet

    elif self.role == LoadBalancingSwitch.DECAP:
      if packet.destination in self.lb_rules and isinstance(packet, EncapSourceDestPacket):
        sd_pkt = packet.pkt
        print self, "Decap received, stripping encapsulation", sd_pkt
        return sd_pkt
      else:
        return packet
    else:
      return packet
    
def LBSwitchClass(base_class):
  class RetClass(base_class, LoadBalancingSwitch):
    def __init__(self, *args):
      base_class.__init__(self, *args)
      LoadBalancingSwitch.__init__(self)

    def receive(self, link, source, packet):
      ret_pkt = LoadBalancingSwitch.receive(self, link, source, packet)
      base_class.receive(self, link, source, ret_pkt)

  return RetClass
