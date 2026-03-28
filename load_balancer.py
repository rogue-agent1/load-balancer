#!/usr/bin/env python3
"""Load balancer simulator (Round Robin, Weighted, Least Connections, Hash) — zero-dep."""
import hashlib

class Server:
    def __init__(self, name, weight=1):
        self.name=name; self.weight=weight; self.connections=0; self.requests=0

class LoadBalancer:
    def __init__(self, servers, algorithm="round_robin"):
        self.servers=[Server(s) if isinstance(s,str) else Server(s[0],s[1]) for s in servers]
        self.algorithm=algorithm; self.rr_idx=0; self.wrr_counter=0
    def next(self, client_ip=None):
        if self.algorithm=="round_robin": return self._round_robin()
        elif self.algorithm=="least_conn": return self._least_conn()
        elif self.algorithm=="ip_hash": return self._ip_hash(client_ip or "0.0.0.0")
        elif self.algorithm=="weighted": return self._weighted()
    def _round_robin(self):
        s=self.servers[self.rr_idx%len(self.servers)]; self.rr_idx+=1
        s.connections+=1; s.requests+=1; return s
    def _least_conn(self):
        s=min(self.servers,key=lambda s:s.connections)
        s.connections+=1; s.requests+=1; return s
    def _ip_hash(self, ip):
        h=int(hashlib.md5(ip.encode()).hexdigest(),16)
        s=self.servers[h%len(self.servers)]; s.connections+=1; s.requests+=1; return s
    def _weighted(self):
        total=sum(s.weight for s in self.servers)
        self.wrr_counter=(self.wrr_counter+1)%total
        cum=0
        for s in self.servers:
            cum+=s.weight
            if self.wrr_counter<cum: s.connections+=1; s.requests+=1; return s

if __name__=="__main__":
    for algo in ["round_robin","least_conn","ip_hash","weighted"]:
        lb=LoadBalancer([("web1",3),("web2",2),("web3",1)],algorithm=algo)
        for i in range(12):
            s=lb.next(client_ip=f"10.0.0.{i%5}")
            if i<3 and algo=="round_robin": s.connections-=1  # simulate disconnect
        dist={s.name:s.requests for s in lb.servers}
        print(f"  {algo:>12}: {dist}")
