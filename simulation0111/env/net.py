from . import Context, FloodPacket
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
  def __repr__ (self):
    return "%s--%s"%(self.a, self.b)
  def SetUp (self):
    if not self.up:
      #print "%f %s UP"%(self.ctx.now, self)
      self.up = True # Set link status to up
      delay = self.ctx.config.DetectionDelay
      self.ctx.schedule_task(delay, lambda: self.a.NotifyUp(self))
      self.ctx.schedule_task(delay, lambda: self.b.NotifyUp(self))
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

