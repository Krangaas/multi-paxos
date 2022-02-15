import hashlib
import os
from itertools import cycle
import argparse
import random
import time
import socket


def parse_hostfile(m_val, env, nodes):
    """ Parse the hostfile and calculate a key for each address """
    K_A = {}
    if env == "cluster":
        # choose a random port from the ephemeral port range
        # suggestet by the Internet Assigned Numbers Authority (IANA)
        port = random.randint(49152, 65535)
        with open('hostfile', mode='r') as f:
            for line in f:
                host = line.splitlines()[0]
                # add port number to addresses
                host = host + ":" + str(port)
                # encode to utf-8,
                # convert to hex,
                # hash with SHA-1,
                # convert to int
                # perform modulo m
                key = int(hashlib.sha1(host.encode()).hexdigest(), 16) % (pow(2, m_val))
                K_A[key] = host
    else:
        hostname = socket.gethostname()
        port = list(range(8000, 8000+nodes))
        for host in range(nodes):
            # add port number to addresses
            host = hostname + ":" + str(port.pop())
            # encode to utf-8,
            # convert to hex,
            # hash with SHA-1,
            # convert to int
            # perform modulo m
            key = int(hashlib.sha1(host.encode()).hexdigest(), 16) % (pow(2, m_val))
            K_A[key] = host

    # write hostname and port to hostfile
    with open('hostfile', mode='w') as f:
        for key, value in K_A.items():
            f.write(str(value) + "\n")
    if len(K_A) == 0:
        print("No addresses in hostfile")
        exit(0)
    return K_A


def concatenate_command(K_A, keylist, env, m_val, throughput, singlemode, die_after_seconds):
    """ Concatenate the system command """
    command = ""
    for i in range(len(keylist)):
        me = K_A[keylist[i]]
        if not singlemode:
            # access entries in key-address dict with sorted keylist and modular arithmetic
            prev = K_A[keylist[(i-1) % len(keylist)]]
            next = K_A[keylist[(i+1) % len(keylist)]]
            next_next = K_A[keylist[(i+2) % len(keylist)]]

        else:
            next = me
            prev = me
            next_next = me

        if env == "local":
            command += ("python3 node.py -p " + me.split(":")[1] + " " + prev +
                        " " + next + " " + next_next + " -m " + str(m_val) + " " +
                        "--die-after-seconds " + str(die_after_seconds) + " ")
        elif env == "cluster":
            command += ("ssh -f " + me.split(":")[0] + " python3 $PWD/node.py -p " +
                        me.split(":")[1] + " " + prev + " " + next + " " + next_next +
                        " -m " + str(m_val) + " " + "--die-after-seconds " + str(die_after_seconds) + " ")
        if throughput == 1:
            command += "-t 1 "
        if i < len(keylist)-1:
            command += "& "
    return command


def main(args):
    """ Main function """
    keylist = [] # initalize empty keylist
    command = "" # initialize empty command string

    # generate hosts
    if (args.environment == "cluster"):
        os.system("./generate_hosts.sh "+str(args.nodes))

    # parse hostfile into dict
    K_A = parse_hostfile(args.mbits, args.environment, args.nodes)

    # sort keys
    keylist = sorted(K_A.keys())

    # concatenate command to initalize the nodes
    command = concatenate_command(K_A, keylist, args.environment, args.mbits, args.throughput,
                                  args.singlemode, args.die_after_seconds)

    if args.debug == 1:
        print(command)
        return

    print("Starting server on the following nodes:")
    for key in keylist:
        print("    ", K_A[key])

    os.system(command)


def parse_args():
    """ optarg parser """
    DIE_AFTER_SECONDS_DEFAULT = 10 * 60
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--environment", required=False, type=str, default="cluster",
        help ="Default: cluster | Specify environment. Valid inputs are: (cluster | local)")

    p.add_argument("-m", "--mbits", type=int, default=10000,
            help ="Default: 10000 | Number of bits m for computing identifier (2^m)")

    p.add_argument("-n", "--nodes", required=False, type=int, default=8,
        help ="Default: 8 | Number of nodes to use")

    p.add_argument("-t", "--throughput", required=False, type=int, default=0,
        help ="Default: 0 | if 1, count throughput")

    p.add_argument("-D", "--debug", required=False, type=int, default=0,
        help ="Default: 0 | if 1, print resultant terminal commands and exit")

    p.add_argument("-s", "--singlemode", required=False, type=int, default=0,
        help ="Default: 0 | if 1, initiate all nodes as a single-node network")

    p.add_argument("--die-after-seconds", type=float,
                   default=DIE_AFTER_SECONDS_DEFAULT,
                   help="kill server after so many seconds have elapsed, " +
                        "in case we forget or fail to kill it, " +
                        "default %d (%d minutes)" % (DIE_AFTER_SECONDS_DEFAULT, DIE_AFTER_SECONDS_DEFAULT/60))

    args = p.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    main(args)
