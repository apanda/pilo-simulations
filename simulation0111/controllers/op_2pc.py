from env import *
from sim import Simulation
import networkx as nx
class Oracle2PC(object):
    __metaclass__ = Singleton
    def __init__(self, ctx):
        self.simulation = Simulation()
        self.delay = 10
        self.ctx = ctx
        self.events = []
        self.number = 0
        self.ctx.schedule_task(self.delay, self.ProcEvents)
        self.replies = {}
        self.registered_controllers = {}
        self.timeout = 10 * self.ctx.config.ControlLatency

    def RegisterController(self, controller):
        self.registered_controllers[controller.name] = controller

    def NotifyEvent(self, controller, event): 
        self.events.append((controller.name, event))

    def ProcEvents(self):
        self.ctx.schedule_task(self.delay * 2, self.ProcEvents)
        if len(self.events) == 0:
            return 
        #print len(self.events)
        event_set = {}
        for c, e in self.events:
            if c not in event_set:
                event_set[c] = []
            event_set[c].append(e)

        for c, events in event_set.iteritems():
            (lambda i, j: self.ctx.schedule_task(
                1, 
                lambda: self.StartPhase1(self.number, i, j)))(c, events)
            self.number += 1

        self.events = []

    def StartPhase1(self, seq, controller, events):
        #print "StartPhase1", seq, len(events)
        components = nx.connected_components(self.simulation.graph)
        controller_set = map(lambda component: \
                             filter(lambda c: c in self.simulation.controller_names, component), \
                             components)[0]
        assert(controller_set != [])
        for c in controller_set:
            latency = self.ctx.config.ControlLatency
            self.ctx.schedule_task(
                latency,
                lambda: self.registered_controllers[c].Phase1Reply(seq, events))

        self.ctx.schedule_task(self.delay, lambda: self.ProcPhase1(seq, controller, controller_set, events, self.timeout))

    def Phase1Reply(self, seq, reply):
        if seq not in self.replies:
            self.replies[seq] = []
        self.replies[seq].append(reply)

    def Abort(self, seq, controller, controller_set, events):
        # Timed out, sends abort to every controller
        latency = self.ctx.config.ControlLatency
        for c in controller_set:
            self.ctx.schedule_task(latency, lambda: self.registered_controllers[c].Phase2Reply(seq, None))

        # re-schedule
        self.replies[seq] = []
        self.ctx.schedule_task(self.delay,
                               lambda: self.StartPhase1(seq, controller, events))

    def ProcPhase1(self, seq, controller, controller_set, events, timeout):
        if timeout == 0:
            self.Abort(seq, controller, controller_set, events)
        else:
            if seq not in self.replies or len(self.replies[seq]) < len(controller_set):
                self.ctx.schedule_task(self.delay,
                                       lambda: self.ProcPhase1(seq, controller, controller_set, events, self.timeout - self.delay))
                return
            # process the replies
            replies = self.replies[seq]
            abort = False
            for r in replies:
                if not r:
                    abort = True
                    break
            if not abort:
                #print "Oracle", seq, controller_set
                latency = self.ctx.config.ControlLatency
                for c in controller_set:
                    (lambda x: self.ctx.schedule_task(latency, 
                                                     lambda: self.registered_controllers[x].Phase2Reply(seq, events)))(c)
            else:
                self.Abort(seq, controller, controller_set, events)                                       

class Controller2PC(LSController):
    def __init__(self, name, ctx, address):
        super(Controller2PC, self).__init__(name, ctx, address)
        self.hosts = set()
        self.controllers = set([self.name])

        # 2PC state
        self.oracle = Oracle2PC(ctx)
        self.in_progress_2pc = -1
        self.timeout_2pc = 1000
        self.oracle.RegisterController(self)
        
    def PacketIn(self, pkt, src, switch, source, packet):
        pass

    def currentLeader (self, switch):
        for c in sorted(list(self.controllers)):
            if c not in self.graph:
                self.graph.add_node(c)
        for c in sorted(list(self.controllers)):
            if nx.has_path(self.graph, c, switch):
                return c #Find the first connected controller

    def Phase1Reply(self, seq, events):
        if self.in_progress_2pc > 0:
            reply = False
        else:
            reply = True
            self.in_progress_2pc = seq
            self.ctx.schedule_task(
                self.timeout_2pc,
                lambda: self.Timeout(seq))

        delay = self.ctx.config.ControlLatency
        self.ctx.schedule_task(
            delay,
            lambda: self.oracle.Phase1Reply(seq, reply))

    def Phase2Reply(self, seq, events):
        if events is None:
            # aborted
            self.in_progress_2pc = False
            return

        #print "Phase2Reply", seq, self, self.graph.nodes()
        # update the current graph
        for e in events:
            event_type = e[-1]
            if event_type == ControlPacket.NotifyLinkUp:
                self.UpdateMembers(e[-3])
                super(Controller2PC, self).addLink(e[-2])
            elif event_type == ControlPacket.NotifyLinkDown:
                self.UpdateMembers(e[-3])
                super(Controller2PC, self).removeLink(e[-2])
            elif event_type == ControlPacket.NotifySwitchUp:
                self.UpdateMembers(e[-2])

        self.ComputeAndUpdatePaths()
        self.in_progress_2pc = False

    def Timeout(self, seq):
        if self.in_progress_2pc == seq:
            self.in_progress_2pc = -1

    def UpdateMembers (self, switch):
        self.graph.add_node(switch.name)
        if isinstance(switch, HostTrait):
            self.hosts.add(switch)
        if isinstance(switch, ControllerTrait):
            self.controllers.add(switch.name)
        
    def NotifySwitchUp (self, pkt, src, switch):
        self.UpdateMembers(switch)
        self.oracle.NotifyEvent(self, (pkt, src, switch, ControlPacket.NotifySwitchUp))

    def NotifyLinkUp (self, pkt, src, switch, link):
        self.UpdateMembers(switch)
        self.oracle.NotifyEvent(self, (pkt, src, switch, link, ControlPacket.NotifyLinkUp))

    def NotifyLinkDown (self, pkt, src, switch, link):
        self.UpdateMembers(switch)
        self.oracle.NotifyEvent(self, (pkt, src, switch, link, ControlPacket.NotifyLinkDown))
        
    def ComputeAndUpdatePaths (self):
        sp = nx.shortest_paths.all_pairs_shortest_path(self.graph)
        for host in self.hosts:
            for h2 in self.hosts:
                if h2 == host:
                    continue
                if h2.name in sp[host.name]:
                    p = SourceDestinationPacket(host.address, h2.address)
                    path = zip(sp[host.name][h2.name], \
                               sp[host.name][h2.name][1:])
                    for (a, b) in path[1:]:
                        link = self.graph[a][b]['link']
                        if self.currentLeader(a) == self.name:
                            self.UpdateRules(a, [(p.pack(), link)])
# A switch that lags
class ControllerLag2PC(Controller2PC):
    def __init__(self, name, ctx, address):
        super(ControllerLag2PC, self).__init__(name, ctx, address)
    
    def Phase1Reply(self, seq, events):
        lag = 5 * self.ctx.config.ControlProc
        self.ctx.schedule_task(lag, lambda: super(ControllerLag2PC, self).Phase1Reply(seq, events))

    def Phase2Reply(self, events):
        lag = 5 * self.ctx.config.ControlProc
        self.ctx.schedule_task(lag, lambda: super(ControllerLag2PC, self).Phase2Reply(seq, events))
