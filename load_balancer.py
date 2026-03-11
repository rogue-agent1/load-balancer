#!/usr/bin/env python3
"""Load balancer: round-robin, weighted, least-connections."""
import sys, random
class Server:
    def __init__(self,name,weight=1): self.name=name; self.weight=weight; self.conns=0; self.total=0
class LB:
    def __init__(self,servers): self.servers=servers; self.idx=0
    def round_robin(self):
        s=self.servers[self.idx%len(self.servers)]; self.idx+=1; return s
    def weighted(self):
        pool=[s for s in self.servers for _ in range(s.weight)]
        s=pool[self.idx%len(pool)]; self.idx+=1; return s
    def least_conn(self):
        return min(self.servers,key=lambda s:s.conns)
servers=[Server('web-1',3),Server('web-2',2),Server('web-3',1)]
lb=LB(servers)
for algo in ['round_robin','weighted','least_conn']:
    for s in servers: s.conns=0; s.total=0
    lb.idx=0
    for _ in range(12):
        s=getattr(lb,algo)(); s.conns+=1; s.total+=1
    print(f"\n{algo}:")
    for s in servers: print(f"  {s.name} (w={s.weight}): {s.total} requests")
