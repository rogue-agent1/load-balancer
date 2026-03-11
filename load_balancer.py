#!/usr/bin/env python3
"""Load balancer — multiple algorithms for distributing requests.

One file. Zero deps. Does one thing well.

Round-robin, weighted round-robin, least connections, random, IP hash,
and power-of-two-choices. Simulates backend health and response times.
"""
import random, hashlib, sys, time
from collections import defaultdict

class Backend:
    __slots__ = ('name', 'weight', 'healthy', 'connections', 'total_requests', 'avg_latency')
    def __init__(self, name, weight=1):
        self.name = name
        self.weight = weight
        self.healthy = True
        self.connections = 0
        self.total_requests = 0
        self.avg_latency = 10.0  # ms

    def handle(self):
        self.connections += 1
        self.total_requests += 1
        latency = self.avg_latency * (1 + self.connections * 0.1)
        self.connections -= 1
        return latency

    def __repr__(self):
        return f"{self.name}(w={self.weight}, conn={self.connections}, reqs={self.total_requests})"

class LoadBalancer:
    def __init__(self, backends):
        self.backends = backends
        self._rr_idx = 0
        self._wrr_idx = 0
        self._wrr_cw = 0

    def _healthy(self):
        return [b for b in self.backends if b.healthy]

    def round_robin(self):
        pool = self._healthy()
        if not pool: return None
        b = pool[self._rr_idx % len(pool)]
        self._rr_idx += 1
        return b

    def weighted_round_robin(self):
        pool = self._healthy()
        if not pool: return None
        max_w = max(b.weight for b in pool)
        gcd_w = pool[0].weight
        for b in pool[1:]:
            a, c = gcd_w, b.weight
            while c: a, c = c, a % c
            gcd_w = a
        while True:
            self._wrr_idx = (self._wrr_idx + 1) % len(pool)
            if self._wrr_idx == 0:
                self._wrr_cw -= gcd_w
                if self._wrr_cw <= 0:
                    self._wrr_cw = max_w
            if pool[self._wrr_idx].weight >= self._wrr_cw:
                return pool[self._wrr_idx]

    def least_connections(self):
        pool = self._healthy()
        if not pool: return None
        return min(pool, key=lambda b: b.connections)

    def random_choice(self):
        pool = self._healthy()
        return random.choice(pool) if pool else None

    def ip_hash(self, client_ip):
        pool = self._healthy()
        if not pool: return None
        h = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return pool[h % len(pool)]

    def power_of_two(self):
        """Power of two random choices — pick 2, use least loaded."""
        pool = self._healthy()
        if not pool: return None
        if len(pool) == 1: return pool[0]
        a, b = random.sample(pool, 2)
        return a if a.connections <= b.connections else b

def simulate(lb, algo_name, algo_fn, n=10000):
    for b in lb.backends:
        b.total_requests = 0
        b.connections = 0
    for _ in range(n):
        if algo_name == "ip_hash":
            b = algo_fn(f"10.0.0.{random.randint(1,255)}")
        else:
            b = algo_fn()
        if b:
            b.connections += 1
            b.connections -= 1
            b.total_requests += 1
    dist = {b.name: b.total_requests for b in lb.backends}
    std = (sum((v - n/len(lb.backends))**2 for v in dist.values()) / len(dist)) ** 0.5
    return dist, std

def main():
    backends = [
        Backend("web-1", weight=5),
        Backend("web-2", weight=3),
        Backend("web-3", weight=2),
        Backend("web-4", weight=1),
    ]
    lb = LoadBalancer(backends)
    n = 10000

    print(f"Load Balancer Comparison ({n:,} requests, 4 backends)\n")
    print(f"{'Algorithm':>20s}  {'web-1':>6s} {'web-2':>6s} {'web-3':>6s} {'web-4':>6s}  {'StdDev':>7s}")
    print("-" * 65)

    random.seed(42)
    algos = [
        ("round_robin", lb.round_robin),
        ("weighted_rr", lb.weighted_round_robin),
        ("least_conn", lb.least_connections),
        ("random", lb.random_choice),
        ("ip_hash", lb.ip_hash),
        ("power_of_two", lb.power_of_two),
    ]
    for name, fn in algos:
        dist, std = simulate(lb, name, fn, n)
        vals = [dist.get(b.name, 0) for b in backends]
        print(f"{name:>20s}  {vals[0]:>6d} {vals[1]:>6d} {vals[2]:>6d} {vals[3]:>6d}  {std:>7.0f}")

    # Health check demo
    print(f"\nHealth check: marking web-2 unhealthy")
    backends[1].healthy = False
    b = lb.round_robin()
    print(f"  round_robin() → {b.name} (skipped unhealthy web-2)")

if __name__ == "__main__":
    main()
