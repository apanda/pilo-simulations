from . import Context, FloodPacket, Switch
"""
Network elements, because why not.
"""
class Host (Switch):
  def __init__ (self, name, ctx, address):
    super(Host, self).__init__(name, ctx)
    self.address = address

  def receive (self, link, source, packet):
    print "Received from %s %s"%(source.name, str(packet))

  def Send (self, packet):
    super(Host, self).Flood(None, packet)

