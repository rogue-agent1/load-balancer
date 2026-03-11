#!/usr/bin/env python3
"""Load Balancer — round-robin, weighted, least-connections, consistent hash."""
import hashlib, random, bisect

class Server:
    def __init__(self, name, weight=1):
        self.name = name; self.weight = weight
        self.connections = 0; self.requests = 0; self.alive = True

class RoundRobin:
    def __init__(self, servers): self.servers = servers; self.idx = 0
    def next(self):
        alive = [s for s in self.servers if s.alive]
        if not alive: return None
        s = alive[self.idx % len(alive)]; self.idx += 1; return s

class WeightedRoundRobin:
    def __init__(self, servers):
        self.pool = []
        for s in servers:
            self.pool.extend([s] * s.weight)
        self.idx = 0
    def next(self):
        alive = [s for s in self.pool if s.alive]
        if not alive: return None
        s = alive[self.idx % len(alive)]; self.idx += 1; return s

class LeastConnections:
    def __init__(self, servers): self.servers = servers
    def next(self):
        alive = [s for s in self.servers if s.alive]
        if not alive: return None
        return min(alive, key=lambda s: s.connections)

class ConsistentHashLB:
    def __init__(self, servers, vnodes=100):
        self.ring = []; self.nodes = {}
        for s in servers:
            for i in range(vnodes):
                h = int(hashlib.md5(f"{s.name}:{i}".encode()).hexdigest(), 16)
                bisect.insort(self.ring, h); self.nodes[h] = s
    def get(self, key):
        h = int(hashlib.md5(str(key).encode()).hexdigest(), 16)
        idx = bisect.bisect(self.ring, h) % len(self.ring)
        return self.nodes[self.ring[idx]]

if __name__ == "__main__":
    servers = [Server("web-1", 1), Server("web-2", 2), Server("web-3", 1)]
    rr = RoundRobin(servers)
    dist = {}
    for _ in range(100):
        s = rr.next(); dist[s.name] = dist.get(s.name, 0) + 1
    print(f"Round Robin: {dist}")
    wrr = WeightedRoundRobin(servers); dist = {}
    for _ in range(100):
        s = wrr.next(); dist[s.name] = dist.get(s.name, 0) + 1
    print(f"Weighted RR: {dist}")
    lc = LeastConnections(servers)
    servers[0].connections = 5; servers[1].connections = 2; servers[2].connections = 8
    print(f"Least Conn: {lc.next().name}")
