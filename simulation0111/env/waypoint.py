from . import Switch, Controller, ControlPacket, FloodPacket, SourceDestinationPacket, MarkedSourceDestPacket, Host

class WaypointSwitch(Switch):
  def __init__(self, name, ctx):
    super(WaypointSwitch, self).__init__(name, ctx)
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
    
class WaypointController(Controller):
  def __init__(self, name, ctx, address):
    super(WaypointController, self).__init__(name, ctx, address)
    self.waypoint_rules = {}

  def updateWaypointRules(self, switch, new_rules):
    self.waypoint_rules = new_rules
    cpacket = ControlPacket(self.cpkt_id, self.name, switch, ControlPacket.UpdateWaypointRules, new_rules)
    self.cpkt_id += 1
    self.sendControlPacket(cpacket)

class WaypointHost(Host):
  def __init__ (self, name, ctx, address):
    super(WaypointHost, self).__init__(name, ctx, address)

  def receive (self, link, source, packet):
    if isinstance(packet, MarkedSourceDestPacket):
      if packet.mark == True:
        print self, " received marked pkt from ", packet.source

    super(WaypointHost, self).receive(link, source, packet)
