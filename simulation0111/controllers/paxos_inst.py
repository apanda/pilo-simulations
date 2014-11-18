class Proposer(object):
    def __init__(self, acceptors):
        self.acceptors = acceptors
        self.n = 0
        self.v = None
        
    def propose(self, v):
        if self.v:
            return self.v

        self.n += 1
        count = 0
        ret = []
        for p in self.acceptors:
            (result, ret_n, ret_v) = p.prepare(self.n)
            if result == "YES":
                count += 1
                if ret_n > 0:
                    ret.append((ret_n, ret_v))

        max_ret_n = -1
        accepted_value = None
        if count > len(self.acceptors) / 2:
            # this proposal was accepted by a majority!
            for (ret_n, ret_v) in ret:
                if max_ret_n == -1:
                    max_ret_n = ret_n
                    accepted_value = ret_v
                    continue
                if max_ret_n < ret_n:
                    max_ret_n = ret_n
                    accepted_value = ret_v

            if accepted_value is None:
                accepted_value = v
            if max_ret_n == -1:
                max_ret_n = self.n

            # send value to all acceptors
            count = 0
            for p in self.acceptors:
                (result, ret_n) = p.accept(max_ret_n, accepted_value)
                if result == "YES":
                    count += 1

            if count > len(self.acceptors) / 2:
                # decided!
                self.v = accepted_value
                return accepted_value

            self.n = max_ret_n
            return None
        self.n = max_ret_n
        return None

class Acceptor(object):
    def __init__(self):
        self.n_proposed = -1
        self.n_accepted = -1
        self.v_accepted = None

    def prepare(self, n):
        if n > self.n_proposed:
            self.n_proposed = n
            return ("YES", self.n_accepted, self.v_accepted)
        return ("NO", self.n_accepted, self.v_accepted)

    def accept(self, n, v):
        if n >= self.n_proposed:
            self.n_proposed = n
            self.n_accepted = n
            self.v_accepted = v
            return ("YES", n)
        return ("NO", None)

a1 = Acceptor()
a2 = Acceptor()
a3 = Acceptor()
p = Proposer([a1, a2, a3])
print p.propose(5)
p2 = Proposer([a1, a2, a3])
p2.n = 5
print p2.propose(3)
