from . import Switch, Controller, ControlPacket, FloodPacket, SourceDestinationPacket, MarkedSourceDestPacket, Host

class WaypointSwitch(Switch):
  def __init__(self, name, ctx):
    super(WaypointSwitch, self).__init__(name, ctx)
    self.waypoint_rules = {}
    self.ctrl_switchboard[ControlPacket.UpdateWaypointRules] = self.updateWaypointRules
    
  def receive(self, link, source, packet):
    if isinstance(packet, MarkedSourceDestPacket):
      if not packet.mark:
        intermediate = None
        print packet.source, packet.destination
        if packet.source in self.waypoint_rules:
          intermediate = self.waypoint_rules[packet.source][0]
        elif packet.destination in self.waypoint_rules:
          intermediate = self.waypoint_rules[packet.source][0]

        print "Routing to intermediate ", intermediate
        if intermediate == self.name:
          packet.mark = True
        elif intermediate is not None:
          # continue routing to intermediate
          cp_packet = SourceDestinationPacket(packet.source, packet.destination)
          match = cp_packet.pack()
          if match in self.rules:
            delay = self.ctx.config.SwitchLatency
            self.ctx.schedule_task(delay, lambda: self.rules[match].Send(self, packet))
            return

    super(WaypointSwitch, self).receive(link, source, packet)

  def processControlMessage (self, link, source, packet):
    if packet.message_type == ControlPacket.UpdateWaypointRules:
      self.updateWaypointRules(source, packet.message)
      return True
    return super(WaypointSwitch, self).processControlMessage(link, source, packet)

  def updateWaypointRules (self, source, new_rules):
    delay = self.ctx.config.UpdateDelay
    self.ctx.schedule_task(delay, lambda: self.waypoint_rules.update(new_rules))
    
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
      if 
