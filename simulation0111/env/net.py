from . import Context, FloodPacket, ControlPacket
from copy import copy
"""
Network elements, because why not.
"""
class Link (object):
  """Represents a link, delays packets and calls receive on the other side"""
  def __init__ (self, ctx, ep1, ep2):
    self.ctx = ctx
    self.a = ep1
    self.b = ep2
    self.up = False
    self.first_up = True
  def __repr__ (self):
    return "%s--%s"%(self.a, self.b)
  def SetUp (self):
    if not self.up:
      #print "%f %s UP"%(self.ctx.now, self)
      self.up = True # Set link status to up
      delay = self.ctx.config.DetectionDelay
      first_up = self.first_up
      self.first_up = False
      self.ctx.schedule_task(delay, lambda: self.a.NotifyUp(self, first_up))
      self.ctx.schedule_task(delay, lambda: self.b.NotifyUp(self, first_up))
  def SetDown (self):
    if self.up:
      #print "%f %s DOWN"%(self.ctx.now, self)
      self.up = False # Set link status to down
      delay = self.ctx.config.DetectionDelay
      self.ctx.schedule_task(delay, lambda: self.a.NotifyDown(self))
      self.ctx.schedule_task(delay, lambda: self.b.NotifyDown(self))
  def Send (self, source, packet):
    assert source == self.a or source == self.b
    other = self.b
    if source == self.b:
      other = self.a
    def deliverInternal(link, source, dest, packet):
      if link.up:
        dest.receive(link, source, packet)
      else:
        source.NotifyDrop(source, packet)
      #else:
        #print "Dropping packet for link from %s-%s"%(source, dest) #FIXME: Use logging
    pkt = copy(packet)
    pkt.path = list(packet.path)
    delay = self.ctx.config.DataLatency
    self.ctx.schedule_task(delay, \
            lambda: deliverInternal(self, source, other, pkt))

class BandwidthLink(Link):
  def __init__(self, ctx, ep1, ep2):
    super(BandwidthLink, self).__init__(ctx, ep1, ep2)
    self.control_packets = {}
    self.other_packets = 0
    self.buf = {ep1: [], ep2: []}

    # bandwidth means that it can process bandwidth packets per proc_rate timesteps
    self.bandwidth = 10
    self.proc_rate = 10
    self.ctx.schedule_task(self.proc_rate, self.Send2)

    self.bandwidth_limit = False

  def Send (self, source, packet):
    assert source == self.a or source == self.b
    other = self.b
    if source == self.b:
      other = self.a

    def deliverInternal(link, source, dest, packet):
      if link.up:
        dest.receive(link, source, packet)
        self.count(packet)
      else:
        source.NotifyDrop(source, packet)

    pkt = copy(packet)
    pkt.path = list(packet.path)
    delay = self.ctx.config.DataLatency
    if self.bandwidth_limit:
      self.ctx.schedule_task(delay, 
                             lambda: self.buf[source].append(pkt))
    else:
      self.ctx.schedule_task(delay, \
                             lambda: deliverInternal(self, source, other, pkt))

  def count(self, packet):
    if isinstance(packet, ControlPacket):
      mtype = packet.message_type
      if mtype not in self.control_packets:
        self.control_packets[mtype] = 0
      self.control_packets[mtype] += 1
    else:
      self.other_packets += 1
    
  def Send2 (self):
    # dequeue a set of packets
    for source, q in self.buf.iteritems():
      dest = self.a
      if self.a == source:
        dest = self.b
      num_packets = min(self.bandwidth, len(q))
      if self.up:
        for p in q[:num_packets]:
          self.count(p)
          dest.receive(self, source, p)
      else:
        for p in q[:num_packets]:
          source.NotifyDrop(source, p)
      self.buf[source]= q[num_packets:]
      
    self.ctx.schedule_task(self.proc_rate, self.Send2)
