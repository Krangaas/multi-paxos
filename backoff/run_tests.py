#!/usr/bin/env python3
import numpy as np
import sys
import os
from argparse import RawTextHelpFormatter
import argparse


class TestRunner:
    "Runs tests"
    def __init__(self, test, config, fails,
                 clients, requests, timeout, n_runs):
        self.test = test
        #c = []
        #for val in config:
        #    if val.isdigit():
        #        c.append(val)
        #self.config = {
        #    "replicas": c[0],
        #    "leaders": c[1],
        #    "acceptors": c[2]
        #}
        self.config = str(config)
        self.clients = str(clients)
        self.requests = str(requests)
        self.tout = str(timeout)
        self.n_runs = str(n_runs)

        if fails:
            fails = int(fails)
            r = str(fails + 1)
            l = str(fails + 1)
            a = str((2 * fails) + 1)
            self.config = r+l+a

        if test == "thr_per_replica":
            self.__thr_per_replica__()
        elif test == "thr_n_clients":
            self.__thr_n_clients__()
        elif test == "simple_run":
            self.__simple_run__()
        else:
            print("No such test:", test)

    def __thr_per_replica__(self):
        print("YO")

    def __thr_n_clients__(self):
        print(self.replicas)

    def __simple_run__(self):
        print("simple_run with config", str(self.config), " timeout:", self.tout)
        print("python3 env.py" + " -r" + self.requests + " -C" + self.config + " -T" + self.tout + " -c" + self.clients)
        os.system("python3 env.py" + " -r" + self.requests + " -C" + self.config + " -T" + self.tout + " -c" + self.clients)


def parse_args():
    p = argparse.ArgumentParser(prog="run_tests",
                                     description="Measure throughput",
                                     formatter_class=RawTextHelpFormatter)

    p.add_argument("-t", "--test", required=False, type=str, default="simple_run",
        help="\nDefault: 'simple_run' \nSpecify which test to run. Valid inputs are:" +
             "\n   'simple_run'" +
             "\n   'thr_per_replica'" +
             "\n   'thr_n_clients'")

    p.add_argument("-C", "--config", required=False, type=str, default="223",
        help="Default: 223 [REPLICAS|LEADERS|ACCEPTORS] \nSpecify configuration of multi-paxos system.")

    p.add_argument("-f", "--fails", required=False, default=False,
        help="Default: False \nSpecify maximum allowed failing nodes (int).\n"+
             "NOTE: Setting this parameter will create a config that supercedes the one given by the user.")

    p.add_argument("-c", "--clients", required=False, type=int, default=3,
        help="Default: 3 \nNumber of connecting clients.")

    p.add_argument("-r", "--requests", required=False, type=int, default=40,
        help="Default: 40 \nNumber of requests to send per client.")

    p.add_argument("-T", "--timeout", required=False, type=float, default=1.0,
        help="Default: 1.0 \nTimeout length before a client sends the next request.")

    p.add_argument("-n", "--n_runs", required=False, type=int, default=1,
        help="Default: 1\nNumber of tests to run.")

    return p.parse_args()

if __name__=='__main__':
    args = parse_args()
    TestRunner(args.test, args.config, args.fails, args.clients, args.requests, args.timeout, args.n_runs)
