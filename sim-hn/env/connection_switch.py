from . import Context, FloodPacket, Link, ControlPacket, Switch,  ControllerTrait, Connection
import networkx as nx
import traceback
""" A connection oriented PILO switch """
class ConnectionSwitch(Switch):
  def __init__ (self, name, ctx):
    # First initialize super
    super(ConnectionSwitch, self).__init__(name, ctx)
    self.active_ctrlr_connections = {} # Active controller connection

  def newControllerRule (self, r, l):
    self.active_ctrlr_connections[r.name] = Connection(self.name, r.name, l, self.conn_man) 
    print "New controller connection"

  def sendToController (self , type, args, controller = None):
    if not controller:
      controller = ControlPacket.AllCtrlId
    # Mark this packet as not currently flooding.
    p = ControlPacket(self.cpkt_id, self.name, controller, type, args, len(self.active_ctrlr_connections) > 0)
    self.cpkt_id += 1
    if (controller == ControlPacket.AllCtrlId and len(self.active_ctrlr_connections) == 0) or \
           controller not in self.active_ctrlr_connections:
      # Flood, don't have any other way to controller
      super(ConnectionSwitch, self).Flood(None, p)
    else:
      if controller == ControlPacket.AllCtrlId:
        succ = True
        connections = self.active_ctrlr_connections.items()
        for (k, v) in connections:
          # Send out the recorded link
          succ |= v.SendMessage(p)
        if not succ:
          self.Flood(None, p)
      else:
        succ = self.active_ctrlr_connections[controller].SendMessage(p)
        if not succ:
          self.Flood(None, p)

