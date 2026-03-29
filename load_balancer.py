#!/usr/bin/env python3
"""Load balancer algorithms — round robin, weighted, least connections."""
import sys, random

class Server:
    def __init__(self, name, weight=1):
        self.name, self.weight = name, weight
        self.connections = 0
        self.total_requests = 0
    def __repr__(self):
        return f"{self.name}(w={self.weight},c={self.connections})"

class RoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.index = 0
    def next(self):
        s = self.servers[self.index % len(self.servers)]
        self.index += 1
        return s

class WeightedRoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.expanded = []
        for s in servers:
            self.expanded.extend([s] * s.weight)
        self.index = 0
    def next(self):
        s = self.expanded[self.index % len(self.expanded)]
        self.index += 1
        return s

class LeastConnections:
    def __init__(self, servers):
        self.servers = servers
    def next(self):
        return min(self.servers, key=lambda s: s.connections)

class RandomLB:
    def __init__(self, servers):
        self.servers = servers
    def next(self):
        return random.choice(self.servers)

def test():
    servers = [Server("A"), Server("B"), Server("C")]
    rr = RoundRobin(servers)
    seq = [rr.next().name for _ in range(6)]
    assert seq == ["A","B","C","A","B","C"]
    ws = [Server("A", 2), Server("B", 1)]
    wrr = WeightedRoundRobin(ws)
    seq2 = [wrr.next().name for _ in range(6)]
    assert seq2.count("A") == 4  # 2/3 of requests
    lc_servers = [Server("X"), Server("Y"), Server("Z")]
    lc_servers[0].connections = 5; lc_servers[1].connections = 2; lc_servers[2].connections = 8
    lc = LeastConnections(lc_servers)
    assert lc.next().name == "Y"
    print("  load_balancer: ALL TESTS PASSED")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Load balancer algorithms")
