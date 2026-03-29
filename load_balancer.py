#!/usr/bin/env python3
"""load_balancer - Load balancing algorithms (round-robin, weighted, least-connections)."""
import sys, random

class Server:
    def __init__(self, name, weight=1):
        self.name = name
        self.weight = weight
        self.connections = 0
        self.healthy = True
    def __repr__(self):
        return f"Server({self.name}, w={self.weight}, c={self.connections})"

class RoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.index = 0
    def next(self):
        healthy = [s for s in self.servers if s.healthy]
        if not healthy:
            return None
        server = healthy[self.index % len(healthy)]
        self.index = (self.index + 1) % len(healthy)
        return server

class WeightedRoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.current_weight = 0
        self.index = -1
    def next(self):
        healthy = [s for s in self.servers if s.healthy]
        if not healthy:
            return None
        total = sum(s.weight for s in healthy)
        gcd = healthy[0].weight
        for s in healthy[1:]:
            a, b = gcd, s.weight
            while b:
                a, b = b, a % b
            gcd = a
        while True:
            self.index = (self.index + 1) % len(healthy)
            if self.index == 0:
                self.current_weight -= gcd
                if self.current_weight <= 0:
                    self.current_weight = max(s.weight for s in healthy)
            if healthy[self.index].weight >= self.current_weight:
                return healthy[self.index]

class LeastConnections:
    def __init__(self, servers):
        self.servers = servers
    def next(self):
        healthy = [s for s in self.servers if s.healthy]
        if not healthy:
            return None
        return min(healthy, key=lambda s: s.connections)

def test():
    servers = [Server("a"), Server("b"), Server("c")]
    rr = RoundRobin(servers)
    seq = [rr.next().name for _ in range(6)]
    assert seq == ["a", "b", "c", "a", "b", "c"]
    # weighted
    ws = [Server("a", 3), Server("b", 1)]
    wrr = WeightedRoundRobin(ws)
    counts = {"a": 0, "b": 0}
    for _ in range(40):
        counts[wrr.next().name] += 1
    assert counts["a"] > counts["b"]
    # least connections
    servers2 = [Server("x"), Server("y"), Server("z")]
    servers2[0].connections = 5
    servers2[1].connections = 2
    servers2[2].connections = 8
    lc = LeastConnections(servers2)
    assert lc.next().name == "y"
    # health check
    servers[1].healthy = False
    rr2 = RoundRobin(servers)
    seq2 = [rr2.next().name for _ in range(4)]
    assert "b" not in seq2
    print("OK: load_balancer")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: load_balancer.py test")
