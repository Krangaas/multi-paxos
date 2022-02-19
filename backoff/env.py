import os, signal, sys, time, threading
from acceptor import Acceptor
from leader import Leader
from message import RequestMessage, DoneMessage
from process import Process
from replica import Replica
from utils import *

# Values are assigned from table 1 in the Paxos Made Moderatly Complex paper.
NFAILS = 2
NACCEPTORS = (2 * NFAILS) + 1
NREPLICAS = NFAILS + 1
NLEADERS = NFAILS + 1
NREQUESTS = 10
NCONFIGS = 1
NCLIENTS = 3

class Env:
    """
    This is the main code in which all processes are created and run. This
    code also simulates a set of clients submitting requests.
    """
    def __init__(self):
        self.procs = {}

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
        #time.sleep(1)

    def run(self):
        initialconfig = Config([], [], [])
        # Create replicas
        c = 0
        for i in range(NREPLICAS):
            pid = "replica %d" % i
            Replica(self, pid, initialconfig)
            initialconfig.replicas.append(pid)
        # Create acceptors (initial configuration)
        for i in range(NACCEPTORS):
            pid = "acceptor %d.%d" % (c,i)
            Acceptor(self, pid)
            initialconfig.acceptors.append(pid)
        # Create leaders (initial configuration)
        for i in range(NLEADERS):
            pid = "leader %d.%d" % (c,i)
            Leader(self, pid, initialconfig)
            initialconfig.leaders.append(pid)
        # Send client requests to replicas
        # ToDo:
            # Multiple clients sending simultaneous requests.
        threads = []
        for i in range(NREQUESTS):
            for c in range(NCLIENTS):
                for r in initialconfig.replicas:
                    t = threading.Thread(target=self.sendClientRequest, args=[i,c,r])
                    threads.append(t)
                    for thread in threads:
                        if not thread.is_alive():
                            thread.start()
                            time.sleep(1)
                    threads.remove(thread)

        for r in initialconfig.replicas:
            pid = "master"
            cmd = Command(pid, 0, str(NREQUESTS*NCLIENTS))
            self.sendMessage(r, DoneMessage(pid,cmd))
            print("Sent",cmd, "from", pid, "to", r)
        # Create new configurations. The configuration contains the
        # leaders and the acceptors (but not the replicas).
        for c in range(1, NCONFIGS):
            config = Config(initialconfig.replicas, [], [])
            threads = []
            # Create acceptors in the new configuration
            for i in range(NACCEPTORS):
                pid = "acceptor %d.%d" % (c,i)
                Acceptor(self, pid)
                config.acceptors.append(pid)
            # Create leaders in the new configuration
            for i in range(NLEADERS):
                pid = "leader %d.%d" % (c,i)
                Leader(self, pid, config)
                config.leaders.append(pid)
            # Send reconfiguration request
            for r in config.replicas:
                pid = "master %d.%d" % (c,i)
                cmd = ReconfigCommand(pid,0,str(config))
                self.sendMessage(r, RequestMessage(pid, cmd))
                time.sleep(1)
            # Send WINDOW noops to speed up reconfiguration
            for i in range(WINDOW-1):
                pid = "master %d.%d" % (c,i)
                for r in config.replicas:
                    cmd = Command(pid,0,"operation noop")
                    self.sendMessage(r, RequestMessage(pid, cmd))
                    time.sleep(1)
            # Send client requests to replicas
            for i in range(NREQUESTS):
                for c in range(NCLIENTS):
                    for r in config.replicas:
                        t = threading.Thread(target=self.sendClientRequest, args=[i,c,r])
                        threads.append(t)
                        for thread in threads:
                            if not thread.is_alive():
                                thread.start()
                                time.sleep(1)
                        threads.remove(thread)


    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exitcode)

def main():
    e = Env()
    e.run()
    signal.signal(signal.SIGINT, e.terminate_handler)
    signal.signal(signal.SIGTERM, e.terminate_handler)
    signal.pause()


if __name__=='__main__':
    main()
