#!/usr/bin/env python3
"""Round-robin and weighted load balancer."""
import sys, socket, threading, time, random

class Backend:
    def __init__(self, host, port, weight=1):
        self.host = host; self.port = port; self.weight = weight
        self.healthy = True; self.connections = 0; self.total = 0; self.errors = 0

class LoadBalancer:
    def __init__(self, listen_port=8080, algorithm="round-robin"):
        self.backends = []; self.listen_port = listen_port
        self.algorithm = algorithm; self.rr_index = 0; self.lock = threading.Lock()

    def add_backend(self, host, port, weight=1):
        self.backends.append(Backend(host, port, weight))

    def next_backend(self):
        with self.lock:
            healthy = [b for b in self.backends if b.healthy]
            if not healthy: return None
            if self.algorithm == "round-robin":
                b = healthy[self.rr_index % len(healthy)]
                self.rr_index += 1; return b
            elif self.algorithm == "weighted":
                total = sum(b.weight for b in healthy)
                r = random.uniform(0, total); cum = 0
                for b in healthy:
                    cum += b.weight
                    if r <= cum: return b
                return healthy[-1]
            elif self.algorithm == "least-conn":
                return min(healthy, key=lambda b: b.connections)

    def health_check(self):
        while True:
            for b in self.backends:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2); s.connect((b.host, b.port)); s.close()
                    b.healthy = True
                except: b.healthy = False
            time.sleep(5)

    def handle(self, client):
        backend = self.next_backend()
        if not backend:
            client.sendall(b"HTTP/1.1 503 Service Unavailable\r\n\r\nNo backends"); client.close(); return
        backend.connections += 1; backend.total += 1
        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((backend.host, backend.port))
            def fwd(src, dst):
                try:
                    while True:
                        data = src.recv(8192)
                        if not data: break
                        dst.sendall(data)
                except: pass
            t1 = threading.Thread(target=fwd, args=(client, remote), daemon=True)
            t2 = threading.Thread(target=fwd, args=(remote, client), daemon=True)
            t1.start(); t2.start(); t1.join(timeout=30)
        except: backend.errors += 1
        finally: backend.connections -= 1; client.close()

    def stats(self):
        lines = [f"{'Backend':20s} {'Status':8s} {'Conn':5s} {'Total':6s} {'Errors':6s}"]
        for b in self.backends:
            s = "UP" if b.healthy else "DOWN"
            lines.append(f"{b.host}:{b.port:<10d} {s:8s} {b.connections:<5d} {b.total:<6d} {b.errors:<6d}")
        return "\n".join(lines)

    def run(self):
        threading.Thread(target=self.health_check, daemon=True).start()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self.listen_port)); sock.listen(50)
        print(f"Load balancer on :{self.listen_port} ({self.algorithm})")
        print(f"Backends: {[(f'{b.host}:{b.port}', b.weight) for b in self.backends]}")
        try:
            while True:
                c, _ = sock.accept()
                threading.Thread(target=self.handle, args=(c,), daemon=True).start()
        except KeyboardInterrupt: print(f"\n{self.stats()}"); sock.close()

def main():
    import argparse
    p = argparse.ArgumentParser(description="Load balancer")
    p.add_argument("-p", "--port", type=int, default=8080)
    p.add_argument("-a", "--algorithm", choices=["round-robin","weighted","least-conn"], default="round-robin")
    p.add_argument("backends", nargs="+", help="host:port[:weight]")
    args = p.parse_args()
    lb = LoadBalancer(args.port, args.algorithm)
    for b in args.backends:
        parts = b.split(":"); host = parts[0]; port = int(parts[1])
        weight = int(parts[2]) if len(parts) > 2 else 1
        lb.add_backend(host, port, weight)
    lb.run()

if __name__ == "__main__": main()
