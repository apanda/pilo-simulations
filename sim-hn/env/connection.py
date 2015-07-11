from . import ConnectionPacket
class ConnectionManager (object):
  def __init__ (self, owner):
    self.connections = {}
    self.connection_by_dest = {}
    self.owner = owner

  def SendPacket (self, packet):
    return self.owner.Send(packet)

  def RegisterConnection (self, connection):
    self.connections[connection.ConnectionID] = connection
    self.connection_by_dest[connection.destination] = connection

  def UnregisterConnection (self, connection):
    del self.connections[connection.ConnectionID]
    del self.connection_by_dest[connection.destination]

  def ReceivePacket (self, packet):

    if packet.flags & ConnectionPacket.Ack > 0: # Is an Ack
      if packet.connID in self.connections:
        self.connections[packet.connID].ReceiveAck(packet)
        return # Do not ACK an ack

    self.SendPacket(ConnectionPacket(self.owner.name, packet.source, packet.connID, ConnectionPacket.Ack, packet.seq, \
      None)) 
    owner.receive(packet.data)

class Connection (object):
  ConnectionID = 0
  def __init__ (self, source, destination, link, manager):
    self.ConnectionID = Connection.ConnectionID + 1
    Connection.ConnectionID += 1
    self.source = source
    self.destination = destination
    self.unacked_packets = {}
    self.seq = 0
    self.manager = manager
    manager.RegisterConnection(self)

  def SendMessage (self, message):
    packet = ConnectionPacket(self.source, self.destination, self.ConnectionID, ConnectionPacket.Data, self.seq, \
        message)
    self.seq += 1
    sent = self.manager.SendPacket(packet)
    if sent:
      self.unacked_packets[packet.seq] = packet
    return sent

  def ReceiveAck (self, message):
    if message.flags & ConnectionPacket.Ack > 0 and message.seq in self.unacked_packets:
      del self.unacked_packets[message.seq]

