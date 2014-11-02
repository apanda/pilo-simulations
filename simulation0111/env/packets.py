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
