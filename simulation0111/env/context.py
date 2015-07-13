import Queue
import yaml
import numpy.random

class Context (object):
  """
  Basic operations for the simulation
  """
  def __init__ (self, initial_task = None, config = None):
    self.queue = Queue.PriorityQueue()
    self.current_time = 0L
    self.final_time = 0L
    self.post_task_check = None
    if initial_task:
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
    while not self.queue.empty() and (self.final_time == 0 or self.current_time < self.final_time):
      (time, task) = self.queue.get_nowait()
      #print "%f event %s"%(time, task)
      self.current_time = time
      task()
      if self.post_task_check:
        self.post_task_check()

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
    return abs(numpy.random.normal(self.mean, self.stdev))

class ExponentialDistribution (Distributions):
  def __init__ (self, yconfig):
    assert yconfig['distro'] == 'exponential'
    self.shape = float(yconfig['shape'])
  @property
  def next(self):
    return numpy.random.exponential(self.shape)

class Config (object):
  """Configuration carries various latencies"""
  distributions = {
     'constant': ConstDistribution,
     'uniform': UniformDistribution,
     'normal': NormalDistribution,
     'exponential': ExponentialDistribution,
  }
  def __init__ (self, fname = None):
    if not fname:
      fname = "config.yml"
    s = open(fname).read()
    configs = yaml.load(s)
    assert 'control_link_latency' in configs
    assert configs['control_link_latency']['distro'] in Config.distributions
    self.control_dist = Config.distributions[configs['control_link_latency']['distro']](configs['control_link_latency'])

    assert 'data_link_latency' in configs
    assert configs['data_link_latency']['distro'] in Config.distributions
    self.data_dist = Config.distributions[configs['data_link_latency']['distro']](configs['data_link_latency'])

    assert 'switch_processing_latency' in configs
    assert configs['switch_processing_latency']['distro'] in Config.distributions
    self.switch_dist = Config.distributions[configs['switch_processing_latency']['distro']](configs['switch_processing_latency'])

    assert 'detection_delay' in configs
    assert configs['detection_delay']['distro'] in Config.distributions
    self.detection_delay = Config.distributions[configs['detection_delay']['distro']](configs['detection_delay'])

    assert 'update_delay' in configs
    assert configs['update_delay']['distro'] in Config.distributions
    self.update_delay = Config.distributions[configs['update_delay']['distro']](configs['update_delay'])
    
    if 'control_processing_latency' in configs:
      self.control_proc = Config.distributions[configs['control_processing_latency']['distro']]\
                                (configs['control_processing_latency'])
    if 'controller_naggle_time' in configs:
      self.controller_nagle_time = float(configs['controller_naggle_time'])
    else:
      # Turn it off by default
      self.controller_nagle_time = 0.0

    if 'controller_switch_info_delay' in configs:
      self.controller_switch_info_delay = float(configs['controller_switch_info_delay'])
    else:
      self.controller_switch_info_delay = 60.0
  @property
  def ControlLatency(self):
    return self.control_dist.next
  @property
  def DataLatency(self):
    return self.data_dist.next
  @property
  def SwitchLatency(self):
    return self.switch_dist.next
  @property
  def DetectionDelay(self):
    return self.detection_delay.next
  @property
  def UpdateDelay(self):
    return self.update_delay.next
  @property
  def ControlProc(self):
    return self.control_proc.next

class ControllerTrait(object):
  """A generic way to refer to all controllers"""

class HostTrait(object):
  """A generic way to refer to all controllers"""
