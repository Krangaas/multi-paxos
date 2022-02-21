#!/usr/bin/env python3
import numpy as np
import re
import sys
import os
from argparse import RawTextHelpFormatter
import argparse
from utils import parse_config


class TestRunner:
    "Runs tests"
    def __init__(self, test, config, fails,
                 clients, requests, timeout, n_runs, debug):
        self.cfg = str(config)
        self.cli = str(clients)
        self.req = str(requests)
        self.tout = str(timeout)
        self.runs = n_runs

        if fails:
            fails = int(fails)
            r = str(fails + 1)
            l = str(fails + 1)
            a = str((2 * fails) + 1)
            self.cfg = r+l+a

        self.cfg_dict = parse_config(self.cfg)

        if debug:
            print("Test:", test, "(" + str(self.runs) + " run(s))")
            print("python3 env.py " + "-r" + self.req + " -C" + self.cfg + " -T" + self.tout + " -c" + self.cli)
            exit(0)

        self.clean_data_files()

        if test == "thr_per_replica":
            self.__thr_per_replica__()
        elif test == "thr_n_clients":
            self.__thr_n_clients__()
        elif test == "simple_test":
            self.__simple_test__()
        else:
            print("No such test:", test)

    def __thr_per_replica__(self):
        os.system("python3 env.py " + "-r" + self.req + " -C" + self.cfg + " -T" + self.tout + " -c" + self.cli)
        os.system("python3 plot_throughput.py" + str(self.cfg_dict["replicas"]))

    def __thr_n_clients__(self):
        for n in range(self.runs):
            os.system("python3 env.py " + "-r" + self.req + " -C" + self.cfg + " -T" + self.tout + " -c" + self.cli)
            self.cli = str(int(self.cli)+5)
        os.system("python3 plot_throughput.py" + str(self.cfg_dict["replicas"]))

    def __simple_test__(self):
        os.system("python3 env.py " + "-r" + self.req + " -C" + self.cfg + " -T" + self.tout + " -c" + self.cli)
        os.system("python3 confirm_consensus.py " + str(self.cfg_dict["replicas"]))

    def clean_data_files(self):
        for r in range(self.cfg_dict["replicas"]):
            file = "thr_replica_" + str(r)
            with open(file, "w") as f:
                f.write("")


def parse_args():
    p = argparse.ArgumentParser(prog="run_tests",
                                     description="Measure throughput",
                                     formatter_class=RawTextHelpFormatter)

    p.add_argument("-t", "--test", required=False, type=str, default="simple_test",
        help="\nDefault: 'simple_run' \nSpecify which test to run. Valid inputs are:" +
             "\n     'simple_test': Start a single run and confirm consensus between replicas." +
             "\n 'thr_per_replica': Start a single run and plot throughput per replica." +
             "\n   'thr_n_clients': Start multiple runs with increasing number of clients and plot throughput per run.")

    p.add_argument("-C", "--config", required=False, type=str, default="223",
        help="Default: 223 [REPLICAS|LEADERS|ACCEPTORS] \nSpecify configuration of multi-paxos system.")

    p.add_argument("-f", "--fails", required=False, default=False,
        help="Default: False \nSpecify maximum allowed failing nodes (int).\n"+
             "NOTE: Setting this parameter will create a config that supercedes the one given by the user.")

    p.add_argument("-c", "--clients", required=False, type=int, default=3,
        help="Default: 3 \nNumber of connecting clients.")

    p.add_argument("-r", "--requests", required=False, type=int, default=10,
        help="Default: 40 \nNumber of requests to send per client.")

    p.add_argument("-T", "--timeout", required=False, type=float, default=1.0,
        help="Default: 1.0 \nTimeout length before a client sends the next request.")

    p.add_argument("-n", "--n_runs", required=False, type=int, default=1,
        help="Default: 1\nNumber of tests to run.")

    p.add_argument("-D", "--debug", required=False, type=bool, default=False,
        help="Default: False \nPrint output commands and exit.")

    return p.parse_args()

if __name__=='__main__':
    args = parse_args()
    TestRunner(args.test, args.config, args.fails, args.clients, args.requests, args.timeout, args.n_runs, args.debug)
