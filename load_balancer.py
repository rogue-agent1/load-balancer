#!/usr/bin/env python3
"""load_balancer — Round-robin, weighted, least-connections LB. Zero deps."""
import random

class Server:
    def __init__(self, name, weight=1):
        self.name, self.weight = name, weight
        self.connections = 0
        self.total_requests = 0
        self.healthy = True

class RoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.idx = 0
    def next(self):
        healthy = [s for s in self.servers if s.healthy]
        if not healthy: return None
        s = healthy[self.idx % len(healthy)]
        self.idx = (self.idx + 1) % len(healthy)
        s.total_requests += 1
        return s

class WeightedRoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.pool = []
        for s in servers:
            self.pool.extend([s] * s.weight)
        self.idx = 0
    def next(self):
        pool = [s for s in self.pool if s.healthy]
        if not pool: return None
        s = pool[self.idx % len(pool)]
        self.idx = (self.idx + 1) % len(pool)
        s.total_requests += 1
        return s

class LeastConnections:
    def __init__(self, servers):
        self.servers = servers
    def next(self):
        healthy = [s for s in self.servers if s.healthy]
        if not healthy: return None
        s = min(healthy, key=lambda s: s.connections)
        s.connections += 1
        s.total_requests += 1
        return s
    def release(self, server):
        server.connections = max(0, server.connections - 1)

class RandomLB:
    def __init__(self, servers):
        self.servers = servers
    def next(self):
        healthy = [s for s in self.servers if s.healthy]
        if not healthy: return None
        s = random.choice(healthy)
        s.total_requests += 1
        return s

def main():
    random.seed(42)
    configs = [
        ("Round Robin", RoundRobin),
        ("Weighted RR", WeightedRoundRobin),
        ("Least Conn", LeastConnections),
        ("Random", RandomLB),
    ]
    print("Load Balancer Simulation (100 requests, 4 servers):\n")
    for name, LBClass in configs:
        servers = [Server("A",3), Server("B",2), Server("C",1), Server("D",1)]
        lb = LBClass(servers)
        for _ in range(100):
            s = lb.next()
            if hasattr(lb, 'release') and random.random() > 0.3:
                lb.release(s)
        dist = {s.name: s.total_requests for s in servers}
        print(f"  {name:<15} {dist}")

if __name__ == "__main__":
    main()
