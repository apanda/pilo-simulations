import Queue
import yaml
import numpy.random

class Context (object):
  """
  Basic operations for the simulation
  """
  def __init__ (self, initial_task, config = None):
    self.queue = Queue.PriorityQueue()
    self.current_time = 0L
    self.queue.put_nowait((self.current_time, initial_task))
    if not config:
      self.config = Config()
    else:
      self.config = config

  def schedule_task (self, delta, task):
    """Schedule task to be run in some time"""
    self.queue.put_nowait((self.current_time + delta, task))

  @property
  def now(self):
    return self.current_time
  
  def run(self):
    while not self.queue.empty():
      (time, task) = self.queue.get_nowait()
      self.current_time = time
      task(self)

class Distributions (object):
  def __init__ (self, yconfig):
    pass
  @property
  def next (self):
    raise NotImplementedError()

class ConstDistribution (Distributions):
  def __init__ (self, yconfig):
    assert yconfig['distro'] == 'constant'
    self.value = float(yconfig['mean'])
  @property
  def next(self):
    return self.value

class UniformDistribution (Distributions):
  def __init__ (self, yconfig):
    assert yconfig['distro'] == 'uniform'
    self.floor = float(yconfig['min'])
    self.ceil = float(yconfig['max'])
  @property
  def next(self):
    return ((numpy.random.randf() * (self.ceil - self.floor)) + self.floor)

class NormalDistribution (Distributions):
  def __init__ (self, yconfig):
    assert yconfig['distro'] == 'normal'
    self.mean = float(yconfig['mean'])
    self.stdev = float(yconfig['stdev'])
  @property
  def next(self):
    return numpy.random.normal(self.mean, self.stdev)

class Config (object):
  """Configuration carries various latencies"""
  distributions = {
     'constant': ConstDistribution,
     'uniform': UniformDistribution,
     'normal': NormalDistribution,
  }
  def __init__ (self, fname = None):
    if not fname:
      fname = "config.yml"
    s = open(fname).read()
    configs = yaml.load(s, Loader=yaml.CLoader)
    assert 'control_link_latency' in configs
    assert configs['control_link_latency']['distro'] in Config.distributions
    self.control_dist = Config.distributions[configs['control_link_latency']['distro']](configs['control_link_latency'])
    assert 'data_link_latency' in configs
    assert configs['data_link_latency']['distro'] in Config.distributions
    self.data_dist = Config.distributions[configs['data_link_latency']['distro']](configs['data_link_latency'])
  @property
  def ControlLatency(self):
    return self.control_dist.next
  @property
  def DataLatency(self):
    return self.data_dist.next
