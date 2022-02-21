import os, signal, sys, time, threading
from acceptor import Acceptor
from leader import Leader
from message import RequestMessage, DoneMessage
from process import Process
from replica import Replica
from utils import *
import argparse

class Env:
    """
    This is the main code in which all processes are created and run. This
    code also simulates a set of clients submitting requests.
    """
    def __init__(self, requests, config, timeout, clients):
        self.procs = {}
        self.NREQUESTS = int(requests)
        self.NACCEPTORS = int(config["acceptors"])
        self.NREPLICAS = int(config["replicas"])
        self.NLEADERS = int(config["leaders"])
        self.timeout = float(timeout)
        self.NCLIENTS = int(clients)

    def sendMessage(self, dst, msg):
        if dst in self.procs:
            self.procs[dst].deliver(msg)

    def addProc(self, proc):
        self.procs[proc.id] = proc
        proc.start()

    def removeProc(self, pid):
        del self.procs[pid]

    def sendClientRequest(self, i, c, r):
        pid = "client %d.%d" % (c,i)
        cmd = Command(pid, 0, "operation %d.%d" % (c, i))
        self.sendMessage(r, RequestMessage(pid,cmd, str(time.time())))
        print("Sent",cmd, "from", pid, "to", r)

    def run(self):
        initialconfig = Config([], [], [])
        # Create replicas
        c = 0
        for i in range(self.NREPLICAS):
            pid = "replica %d" % i
            Replica(self, pid, initialconfig)
            initialconfig.replicas.append(pid)
        # Create acceptors (initial configuration)
        for i in range(self.NACCEPTORS):
            pid = "acceptor %d.%d" % (c,i)
            Acceptor(self, pid)
            initialconfig.acceptors.append(pid)
        # Create leaders (initial configuration)
        for i in range(self.NLEADERS):
            pid = "leader %d.%d" % (c,i)
            Leader(self, pid, initialconfig)
            initialconfig.leaders.append(pid)
        # Send client requests to replicas
        threads = []
        for i in range(self.NREQUESTS):
            for c in range(self.NCLIENTS):
                for r in initialconfig.replicas:
                    t = threading.Thread(target=self.sendClientRequest, args=[i,c,r])
                    threads.append(t)
                    for thread in threads:
                        if not thread.is_alive():
                            thread.start()
                            time.sleep(self.timeout)
                    threads.remove(thread)

        for r in initialconfig.replicas:
            pid = "master"
            cmd = Command(pid, self.NCLIENTS, str(self.NREQUESTS*self.NCLIENTS))
            self.sendMessage(r, DoneMessage(pid,cmd))
            print("Sent",cmd, "from", pid, "to", r)


    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exitcode)

def parse_args():
    """ optarg parser """
    p = argparse.ArgumentParser()
    p.add_argument("-r", "--requests", required=True, type=int,
        help = "Number of requests to send per client.")
    p.add_argument("-C", "--config", required=True, type=str,
        help="Specify configuration of multi-paxos system.")
    p.add_argument("-T", "--timeout", required=True, type=float,
        help="Timeout length before a client sends the next request.")
    p.add_argument("-c", "--clients", required=True, type=int,
        help="Number of connecting clients.")

    return p.parse_args()

def main(args):

    args.config = parse_config(args.config)

    e = Env(args.requests, args.config, args.timeout, args.clients)
    e.run()
    signal.signal(signal.SIGINT, e.terminate_handler)
    signal.signal(signal.SIGTERM, e.terminate_handler)
    signal.pause()

if __name__=='__main__':
    args = parse_args()
    main(args)
