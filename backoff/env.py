import os, signal, sys, time
from acceptor import Acceptor
from leader import Leader
from message import RequestMessage
from process import Process
from replica import Replica
from utils import *
import argparse

# Values are assigned from table 1 in the Paxos Made Moderatly Complex paper.
NFAILS = None
NACCEPTORS = None
NREPLICAS = None
NLEADERS = None
NREQUESTS = None
NCONFIGS = None

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

    def run(self):
        initialconfig = Config([], [], [])
        c = 0

        # Create replicas
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
        for i in range(NREQUESTS):
            pid = "client %d.%d" % (c,i)
            for r in initialconfig.replicas:
                cmd = Command(pid,0,"operation %d.%d" % (c,i))
                self.sendMessage(r, RequestMessage(pid,cmd))
                time.sleep(1)

        # Create new configurations. The configuration contains the
        # leaders and the acceptors (but not the replicas).
        for c in range(1, NCONFIGS):
            config = Config(initialconfig.replicas, [], [])
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
                pid = "client %d.%d" % (c,i)
                for r in config.replicas:
                    cmd = Command(pid,0,"operation %d.%d"%(c,i))
                    self.sendMessage(r, RequestMessage(pid, cmd))
                    time.sleep(1)

    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exitcode)

def main(args):
    global NACCEPTORS
    global NREPLICAS
    global NLEADERS
    global NCONFIGS
    global NREQUESTS
    global NFAILS
    NFAILS = args.fails
    NREQUESTS = args.requests
    NCONFIGS = args.configs
    NACCEPTORS = (2 * NFAILS) + 1
    NREPLICAS = NFAILS + 1
    NLEADERS = NFAILS + 1
    e = Env()
    e.run()
    signal.signal(signal.SIGINT, e.terminate_handler)
    signal.signal(signal.SIGTERM, e.terminate_handler)
    signal.pause()

def parse_args():
    """ optarg parser """
    DIE_AFTER_SECONDS_DEFAULT = 10 * 60
    p = argparse.ArgumentParser()
    p.add_argument("-R", "--roles", required=False, type=list, default=[2,2,3],
        help = "Default: 223 | Configuration of roles. " +
               "Valid input is: [NREPLICAS][NLEADERS][NACCEPTORS]")
    p.add_argument("-t", "--test", required=False, type=str, default=None,
        help = "Default: None | Specify which test to run. " +
               "Valid inputs are: (throughput | ...)")
    p.add_argument("-r", "--requests", required=False, type=int, default=40,
        help = "Default: 40 | Number of requests to send.")
    p.add_argument("-f", "--fails", required=False, type=int, default=1,
        help = "Default: 1 | Number of acceptable fails.")
    p.add_argument("-c", "--configs", required=False, type=int, default=3,
        help = "Default: 1 | Number of role configurations to try.")
    p.add_argument("-C", "--clients", required=False, type=int, default=1,
        help = "Default: 1 | Number of clients.")
    args = p.parse_args()
    return args

if __name__=='__main__':
    args = parse_args()
    main(args)
