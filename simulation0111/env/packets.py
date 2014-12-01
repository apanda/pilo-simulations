import struct
"""
Packet representations we care about
"""

class Packet (object):
  """Represent whatever interesting fields
     one cares about in a packet"""
  def __init__ (self):
    self.ttl = 255
    self.path = []
  def __eq__ (self, A):
    return hash(A) == hash(self)
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
    return str(self.id)
  def __hash__ (self):
    return hash((self.id))
  def pack (self):
    return id

class ControlPacket (FloodPacket):
  """Packets signifying in-band control messages"""
  ForwardPacket = 1
  UpdateRules = 2
  NotifySwitchUp = 3
  NotifyLinkDown = 4
  NotifyLinkUp = 5
  PacketIn = 6
  GetSwitchInformation = 7
  SwitchInformation = 8
  SetSwitchLeader = 9
  AckSetSwitchLeader = 10
  RequestRelinquishLeadership = 11
  AckRelinquishLeadership = 12
  AllCtrlId = "ALL",
  UpdateWaypointRules = 13,
  Propose = 14,
  Accept = 15,
  Decide = 16,
  ProposeReply = 17,
  AcceptReply = 18,
  PaxosMaxSeq = 19,
  NackUpdateRules = 20,
  def __init__ (self, id, src_id, dest_id, mtype, message):
    super(ControlPacket, self).__init__(id)
    self.src_id = src_id
    self.dest_id = dest_id
    self.message_type = mtype
    self.message = message
  def __str__ (self):
    return 'CP %s %s'%(str(self.id), self.src_id)
  def __hash__ (self):
    return hash((self.id, self.src_id, self.dest_id, self.message_type))
  def pack (self):
    return struct.pack("ss", \
             self.src_id, \
             self.dest_id)

class SourceDestinationPacket (Packet):
  """Simple packet with a source and destination (both 
  unsigned longs)"""
  ID = 0
  def __init__(self, source, destination):
    super(SourceDestinationPacket, self).__init__()
    self.source = source
    self.destination = destination
    self.ID = SourceDestinationPacket.ID + 1
    SourceDestinationPacket.ID += 1
  def __hash__ (self):
    return hash((self.ID, self.source, self.destination))
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

class HeartbeatPacket (FloodPacket): 
  def __init__ (self, id, src, direct_links, heard_from, sobj):
    super(HeartbeatPacket, self).__init__(id)
    self.src = src
    self.direct_links = direct_links
    self.heard_from = heard_from
    self.sobj = sobj
  def __hash__ (self):
    return hash(( self.id, self.src))
  def pack (self):
    return struct.pack("s", \
             self.src)
