from . import Context, FloodPacket, Switch, SourceDestinationPacket, ControlPacket, HostTrait
class Host (Switch, HostTrait):
  """A generic host. Hosts in general don't have access to layer A functionality (but in the case of heartbeats
  must participate in that protocol"""
  def __init__ (self, name, ctx, address):
    super(Host, self).__init__(name, ctx)
    self.address = address
    self.send_callback = None
    self.recv_callback = None

  def receive (self, link, source, packet):
    if isinstance(packet, SourceDestinationPacket):
      if self.recv_callback:
        self.recv_callback(self, packet)
      #print "%f %s Received from %d to %d"%(self.ctx.now, self.name, packet.source, packet.destination)
    elif isinstance(packet, ControlPacket):
      self.processControlMessage (link, source, packet)

  def Send (self, packet):
    if isinstance(packet, SourceDestinationPacket) and self.send_callback:
      self.send_callback(self, packet)
    super(Host, self).Flood(None, packet)

