from env import *
from ls_ldr_controller import LSLeaderControl
import networkx as nx
import random
import copy

class PaxosInst(object):
    IN_PROGRESS = 1
    FAIL = 2
    SUCCESS = 3
    
    def __init__(self):
        self.n = 0
        self.v_p = None

        self.n_proposed = -1
        self.n_accepted = -1
        self.v_accepted = None

        self.propose_1_replies = []
        self.propose_2_replies = []

        self.p_status = PaxosInst.IN_PROGRESS

        self.decided_value = None
        self.decided = False

    def clear_proposer(self):
        self.v_p = None

        self.propose_1_replies = []
        self.propose_2_replies = []

class PaxosController(LSLeaderControl):
    def __init__(self, name, ctx, address):
        super(PaxosController, self).__init__(name, ctx, address)
        self.hosts = set()
        self.controllers = set([self.name])
        self.current_rules = {}

        # Paxos
        self.is_leader = False
        self.paxos_inst = {}
        self.timeout = 1500
        self.delay = 10
        self.log = {}
        self.seq = 0
        self.max_seq_replayed = 0

        self.switchboard[ControlPacket.Propose] = self.prepare
        self.switchboard[ControlPacket.Accept] = self.accept
        self.switchboard[ControlPacket.Decide] = self.decide
        self.switchboard[ControlPacket.ProposeReply] = self.processPaxosMessage
        self.switchboard[ControlPacket.AcceptReply] =self.processPaxosMessage

        self.ctx.schedule_task(self.delay, self.learn)
        self.ctx.schedule_task(self.delay, self.replay_logs)

    def CalcNewRules(self):
        rules = {}
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
                        rules[(a, p.pack())] = link
        #print rules
        #raw_input()
        return rules

    def ComputeAndUpdatePaths(self):
        # calculate new paths, then use consensus to reach agreement
        rules = self.CalcNewRules()
        self.seq += 1
        self.propose(self.seq, rules)

    def propose(self, seq, proposed_value):
        if seq not in self.paxos_inst:
            self.paxos_inst[seq] = PaxosInst()
        else:
            self.paxos_inst[seq].clear_proposer()

        px = self.paxos_inst[seq]

        if px.decided or px.p_status == PaxosInst.SUCCESS:
            return 

        px.n += random.randint(0, 100)
        px.v_p = proposed_value

        # flood to all controllers
        # msg format: {source, sequence number, n}
        
        self.ctx.schedule_task(self.delay, 
                               lambda: self.sendToController(
                                   ControlPacket.Propose, 
                                   [seq, px.n, self.name]))

        # schedule self
        self.ctx.schedule_task(self.delay, 
                               lambda: self.prepare(None, None, seq, px.n, self.name))
        self.ctx.schedule_task(self.timeout, lambda: self.propose_1(seq))

    def propose_1(self, seq):
        accept_count = 0
        px = self.paxos_inst[seq]

        #print ">>>>>>>>>", self, "propose_1", seq, px.propose_1_replies, "<<<<<<<<<<<"

        ret = []
        for r in px.propose_1_replies:
            (reply, n_a, v_a) = r["reply"]
            if reply:
                accept_count += 1
                if n_a > -1:
                    ret.append((n_a, v_a))

        if accept_count > len(self.controllers) / 2:
            max_n_a = -1
            max_v_a = None
            for (n_a, v_a) in ret:
                if n_a > max_n_a:
                    max_n_a = n_a
                    max_v_a = v_a

            if max_n_a < 0:
                # choose any value 
                max_v_a = px.v_p
            else:
                px.v_p = max_v_a
            
            # schedule propose 2 round
            self.ctx.schedule_task(self.delay, 
                                   lambda: self.sendToController(
                                       ControlPacket.Accept,
                                       [seq, px.n, max_v_a, self.name]
                                   ))
            # send to self
            self.ctx.schedule_task(self.delay, 
                                   lambda: self.accept(None, None, seq, px.n, max_v_a, self.name))
            self.ctx.schedule_task(self.timeout,
                                   lambda: self.propose_2(seq))
            return

        px.p_status = PaxosInst.FAIL
        self.ctx.schedule_task(self.delay, lambda: self.propose(seq, px.v_p))

    def propose_2(self, seq):
        px = self.paxos_inst[seq]
        accept_count = 0

        for r in px.propose_2_replies:
            (reply, n_a) = r["reply"]
            if reply:
                accept_count += 1
        if accept_count > len(self.controllers) / 2:
            # value has been decided!
            px.p_status = PaxosInst.SUCCESS
            self.ctx.schedule_task(self.delay, 
                                   lambda: self.sendToController(
                                       ControlPacket.Decide,
                                       [seq, px.v_p]))
            self.ctx.schedule_task(self.delay,
                                   lambda: self.decide(None, None, seq, px.v_p))
            return

        px.p_status = PaxosInst.FAIL
        self.ctx.schedule_task(self.delay, lambda: self.propose(seq, px.v_p))

    def processPaxosMessage(self, pkt, src, seq, reply):
        if reply["dest"] != self.name:
            return 
        if pkt.message_type == ControlPacket.ProposeReply:
            self.paxos_inst[seq].propose_1_replies.append(reply)
        elif pkt.message_type == ControlPacket.AcceptReply:
            self.paxos_inst[seq].propose_2_replies.append(reply)
        #print seq, self.paxos_inst[seq].propose_1_replies, pkt.message_type

    # acceptor
    def prepare(self, pkt, src, seq, n, source):
        if seq not in self.paxos_inst:
            self.paxos_inst[seq] = PaxosInst()
        px = self.paxos_inst[seq]
        if n > px.n_proposed:
            px.n_proposed = n
            reply = {
                "source": self.name,
                "dest": source,
                "reply": (True, px.n_accepted, px.v_accepted),
            }
            self.ctx.schedule_task(self.delay, 
                                   lambda: self.sendToController(
                                       ControlPacket.ProposeReply,
                                       [seq, reply]
                                   ))

            if source == self.name:
                # schedule self
                self.ctx.schedule_task(self.delay,
                                       lambda: self.processPaxosMessage(
                                           ControlPacket(0, 0, 0, ControlPacket.ProposeReply, [seq, reply]),
                                           0,
                                           seq,
                                           reply))
        else:
            reply = {
                "source": self.name,
                "dest": source,
                "reply": (False, -1, -1)
            }
            self.ctx.schedule_task(self.delay, 
                                   lambda: self.sendToController(
                                       ControlPacket.ProposeReply,
                                       [seq, reply]
                                   ))
            if source == self.name:
                # schedule self
                self.ctx.schedule_task(self.delay,
                                       lambda: self.processPaxosMessage(
                                           ControlPacket(0, 0, 0, ControlPacket.ProposeReply, [seq, reply]),
                                           0,
                                           seq,
                                           reply))
        
    # acceptor
    def accept(self, pkt, src, seq, n, v, source):
        assert (seq in self.paxos_inst)
        px = self.paxos_inst[seq]
        if n >= px.n_proposed:
            px.n_proposed = n
            px.n_accepted = n
            px.v_accepted = v
            reply = {
                "source": self.name,
                "dest": source,
                "reply": (True, px.n_accepted)
            }
            self.ctx.schedule_task(self.delay,
                                   lambda: self.sendToController(
                                       ControlPacket.AcceptReply,
                                       [seq, reply]
                                ))

            if source == self.name:
                # schedule self
                self.ctx.schedule_task(self.delay,
                                       lambda: self.processPaxosMessage(
                                           ControlPacket(0, 0, 0, ControlPacket.ProposeReply, [seq, reply]),
                                           0,
                                           seq,
                                           reply))
        else:
            reply = {
                "source": self.name,
                "dest": source,
                "reply": (False, px.n_proposed)
            }
            self.ctx.schedule_task(self.delay,
                                   lambda: self.sendToController(
                                       ControlPacket.AcceptReply,
                                       [seq, reply]
                                   ))
            if source == self.name:
                # schedule self
                self.ctx.schedule_task(self.delay,
                                       lambda: self.processPaxosMessage(
                                           ControlPacket(0, 0, 0, ControlPacket.ProposeReply, [seq, reply]),
                                           0,
                                           seq,
                                           reply))

    def decide(self, pkt, src, seq, value):
        px = self.paxos_inst[seq]
        px.decided = True
        px.decided_value = value
        #print self, seq, px.decided_value

    def learn(self):
        for seq, px in self.paxos_inst.iteritems():
            if px.decided and seq not in self.log:
                self.log[seq] = px.decided_value

        self.ctx.schedule_task(self.delay * 5, self.learn)

    def replay_logs(self):
        old_max_seq = self.max_seq_replayed
        for i in sorted(self.log.keys()):
            if i == self.max_seq_replayed + 1:
                self.current_rules = self.log[i]
                self.max_seq_replayed += 1

        if old_max_seq < self.max_seq_replayed:
            #print self.max_seq_replayed
            for k, link in self.current_rules.iteritems():
                (a, p) = k
                self.UpdateRules(a, [(p, link)])
            
            print self, "replayed up to ", self.max_seq_replayed

        self.ctx.schedule_task(self.delay * 5, self.replay_logs)

    # correctness check
    @staticmethod
    def assert_rules(controllers):
        for c1 in controllers:
            for c2 in controllers:
                if len(set(c1.current_rules.items()).difference(set(c2.current_rules.items()))) > 0:
                    print c1, "-", c2
