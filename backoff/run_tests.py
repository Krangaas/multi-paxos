#!/usr/bin/env python3
import numpy as np
import re
import sys
import os
from argparse import RawTextHelpFormatter
import argparse
from utils import parse_config, create_config


class TestRunner:
    "Runs tests"
    def __init__(self, test, config, fails,
                 clients, requests, timeout, runs, increment, debug):
        self.cfg = str(config)
        self.cli = str(clients)
        self.req = str(requests)
        self.tout = str(timeout)
        self.runs = runs
        self.i = increment

        if fails:
            fails = int(fails)
            r = str(fails + 1)
            l = str(fails + 1)
            a = str((2 * fails) + 1)
            self.cfg = r+l+a

        self.cfg_dict = parse_config(self.cfg)

        if debug:
            print("Test: %s, runs: %d (increment %d)" % (test, self.runs, self.i))
            print("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))
            exit(0)

        self.clean_data_files()

        if test == "simple_test":
            self._simple_test_()
        elif test == "thr_per_replica":
            self._thr_per_replica_()
        elif test == "clients":
            self._thr_inc_clients_()
        elif test == "replicas":
            self._thr_inc_replicas_()
        elif test == "leaders":
            self._thr_inc_leaders_()
        elif test == "acceptors":
            self._thr_inc_acceptors_()
        else:
            print("No such test:", test)


    def _simple_test_(self):
        """ Simple run of the multi-paxos algorithm. Confirms that the replicas reached a consensus. """
        os.system("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))
        os.system("python3 confirm_consensus.py %s" % (str(self.cfg_dict["replicas"])))


    def _thr_per_replica_(self):
        """ Simple run of the multi-paxos algorithm. Plots the throughput per replica. """
        os.system("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))
        os.system("python3 plot_throughput.py %s" % (str(self.cfg_dict["replicas"])))


    def _thr_inc_clients_(self):
        """ Multiple runs of the multi-paxos algorithm. Plots throughput as a function of clients. """
        for n in range(self.runs):
            os.system("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))
            self.cli = str(int(self.cli)+self.i)

        title = "'Throughput as as function of clients\n(timeout %s secs, config %s)'" % (self.tout, self.cfg)
        print("python3 plot_throughput.py %s %s" % (str(self.cfg_dict["replicas"]), title))
        os.system("python3 plot_throughput.py %s %s" % (str(self.cfg_dict["replicas"]), title))


    def _thr_inc_replicas_(self):
        """ Multiple runs of the multi-paxos algorithm. Plots throughput as a function of replicas. """
        for n in range(self.runs):
            os.system("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))
            d = parse_config(self.cfg)
            self.cfg = create_config(d["replicas"]+self.i, d["leaders"], d["acceptors"])

        os.system("python3 plot_throughput.py %s %s" % (str(self.cfg_dict["replicas"]), title))


    def _thr_inc_leaders_(self):
        """ Multiple runs of the multi-paxos algorithm. Plots throughput as a function of leaders. """
        for n in range(self.runs):
            os.system("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))
            d = parse_config(self.cfg)
            self.cfg = create_config(d["replicas"], d["leaders"]+self.i, d["acceptors"])
            print("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))

        os.system("python3 plot_throughput.py %s" % (str(self.cfg_dict["replicas"])))


    def _thr_inc_acceptors_(self):
        """ Multiple runs of the multi-paxos algorithm. Plots throughput as a function of acceptors. """
        for n in range(self.runs):
            os.system("python3 env.py -r%s -C%s -T%s -c%s" % (self.req, self.cfg, self.tout ,self.cli))
            d = parse_config(self.cfg)
            self.cfg = create_config(d["replicas"], d["leaders"], d["acceptors"]+self.i)

        os.system("python3 plot_acceptors.py %s" % (str(self.cfg_dict["replicas"])))


    def clean_data_files(self):
        """ Empties the throughput data files. """
        for r in range(self.cfg_dict["replicas"]):
            file = "thr_replica_" + str(r)
            with open(file, "w") as f:
                f.write("")


def parse_args():
    p = argparse.ArgumentParser(prog="run_tests",
        description="Measure throughput for various configurations of the multi-paxos system",
        formatter_class=RawTextHelpFormatter)

    p.add_argument("-t", "--test", required=False, type=str, default="simple_test",
        help="\nDefault: 'simple_run' \nSpecify which test to run. Valid inputs are:" +
             "\n     'simple_test': Start a single run and confirm consensus between replicas." +
             "\n 'thr_per_replica': Start a single run and plot throughput per replica." +
             "\n         'clients': Increment number of clients per run and plot throughput." +
             "\n        'replicas': Increment number of replicas per run and plot throughput" +
             "\n         'leaders': Increment number of leaders per run and plot throughput" +
             "\n       'acceptors': Increment number of acceptors per run and plot throughput")

    p.add_argument("-C", "--config", required=False, type=str, default="223",
        help="Default: 223 [REPLICAS|LEADERS|ACCEPTORS] \nSpecify configuration of multi-paxos system.")

    p.add_argument("-f", "--fails", required=False, default=False,
        help="Default: False \nSpecify maximum allowed failing nodes (int).\n"+
             "NOTE: Setting this parameter will create a config that supercedes the one given by the user.")

    p.add_argument("-c", "--clients", required=False, type=int, default=3,
        help="Default: 3 \nNumber of connecting clients.")

    p.add_argument("-r", "--requests", required=False, type=int, default=100,
        help="Default: 100 \nTotal requests to send.")

    p.add_argument("-T", "--timeout", required=False, type=float, default=1.0,
        help="Default: 1.0 \nTimeout length before a client sends the next request.")

    p.add_argument("-n", "--runs", required=False, type=int, default=3,
        help="Default: 1\nNumber of tests to run.")

    p.add_argument("-i", "--increment", required=False, type=int, default=5,
        help="Default: 3 \nVariable server increment per run. Depending on the  test specified, "+
        "this value will increment either the number of clients, replicas, leaders or acceptors.")

    p.add_argument("-D", "--debug", required=False, type=bool, default=False,
        help="Default: False \nPrint output commands and exit.")

    return p.parse_args()


if __name__=='__main__':
    args = parse_args()
    TestRunner(args.test, args.config, args.fails, args.clients, args.requests,
               args.timeout, args.runs, args.increment, args.debug)
