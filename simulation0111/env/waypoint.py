from . import Switch, Controller, ControlPacket, FloodPacket, SourceDestinationPacket, MarkedSourceDestPacket, Host

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

  return WaypointHost
