from . import Context, FloodPacket, Link, ControlPacket, ConnectionSwitch
import networkx as nx
"""A collection of links state switches"""
class LinkStateSwitch (ConnectionSwitch):
  """Layer A switch for link state"""
  def __init__ (self, name, ctx):
    super(LinkStateSwitch, self).__init__(name, ctx)
    self.g = nx.Graph()
    self.g.add_node(self.name)
    self.controllers = set()
  
  @property
  def graph (self):
    return self.g

  def removeLink (self, link):
    if self.g.has_edge(link.a.name, link.b.name):
      self.g.remove_edge(link.a.name, link.b.name)
    if isinstance(link.a, ControllerTrait):
      self.controllers.add(link.a.name)
    if isinstance(link.b, ControllerTrait):
      self.controllers.add(link.b.name)
    if link.a.name not in self.g:
      self.g.add_node(link.a.name)
    if link.b.name not in self.g:
      self.g.add_node(link.b.name)

  def addLink (self, link):
    self.g.add_edge(link.a.name, link.b.name, link=link)
    if isinstance(link.a, ControllerTrait):
      self.controllers.add(link.a.name)
    if isinstance(link.b, ControllerTrait):
      self.controllers.add(link.b.name)

  def updateRules (self, source, match_action_pairs):
      super(LinkStateSwitch, self).updateRules(source, match_action_pairs)


  def NotifyDown (self, link, version):
    super(LinkStateSwitch, self).NotifyDown(link, version)

  def NotifyUp (self, link, first_up, version):
    super(LinkStateSwitch, self).NotifyUp(link, first_up, version)
