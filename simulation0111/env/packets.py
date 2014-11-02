import struct
"""
Packet representations we care about
"""

class Packet (object):
  """Represent whatever interesting fields
     one cares about in a packet"""
  def __init__ (self):
    self.ttl = 255
  def pack (self):
    """Return a single string on which matches
       are performed"""
    # By default everything matches.
    return ""

class FloodPacket (Packet):
  """Test packet intended to allow flooding"""
  def __init__ (self, id):
    super(FloodPacket, self).__init__()
    self.id = id
  def __str__ (self):
    return self.id
  def pack (self):
    return id

class ControlPacket (Packet):
  """Packets signifying in-band control messages"""
  def __init__ (self, controller_id, destination_id, message):
    super(ControlPacket, self).__init__()
    self.controller_id = controller_id
    self.destination_id = destination_id
    self.message = message
  def pack (self):
    return struct.pack("ss", \
             self.controller_id, \
             self.destination_id)

class SourceDestinationPacket (Packet):
  """Simple packet with a source and destination (both 
  unsigned longs)"""
  def __init__(self, source, destination):
    super(SourceDestinationPacket, self).__init__()
    self.source = source
    self.destination = destination
  def __str__ (self):
    return "SD Packet %d %d"%(self.source, self.destination)
  def pack (self):
    return struct.pack("LL", self.source, \
            self.destination)

class MarkedSourceDestPacket (SourceDestinationPacket):
  """Packet with mark (for waypointing) and source and destination"""
  def __init__(self, source, destination):
    super(MarkedSourceDestPacket, self).__init__(source, destination)
    self.mark = False
  def __str__ (self):
    return "SD Packet %d %d %s"%(self.source, self.destination, str(self.mark))
  def set_mark (self):
    self.mark = True
  def pack (self):
    return super(MarkedSourceDestPacket, self).pack() + struct.pack("?", self.mark)
