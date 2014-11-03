from . import Context, FloodPacket, Switch, SourceDestinationPacket
"""
Network elements, because why not.
"""
class Host (Switch):
  def __init__ (self, name, ctx, address):
    super(Host, self).__init__(name, ctx)
    self.address = address

  def receive (self, link, source, packet):
    if isinstance(packet, SourceDestinationPacket):
      print "%f %s Received from %d to %d"%(self.ctx.now, self.name, packet.source, packet.destination)

  def Send (self, packet):
    super(Host, self).Flood(None, packet)

