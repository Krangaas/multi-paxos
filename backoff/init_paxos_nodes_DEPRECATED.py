import hashlib
import os
from itertools import cycle
import argparse
import random
import time
import socket

def parse_hostfile(env, nodes):
    """ Parse the hostfile and calculate a key for each address """
    hosts = []
    if env == "cluster":
        # choose a random port from the ephemeral port range
        # suggestet by the Internet Assigned Numbers Authority (IANA)
        port = random.randint(49152, 65535)
        with open('hostfile', mode='r') as f:
            for line in f:
                host = line.splitlines()[0]
                # add port number to addresses
                host = host + ":" + str(port)
                hosts.append(host)
    else:
        hostname = socket.gethostname()
        port = list(range(8000, 8000+nodes))
        for host in range(nodes):
            # add port number to addresses
            host = hostname + ":" + str(port.pop())
            hosts.append(host)

    # write hostname and port to hostfile
    with open('hostfile', mode='w') as f:
        for host in hosts:
            f.write(str(host) + "\n")
    if len(hosts) == 0:
        print("No addresses in hostfile")
        exit(0)

    print(hosts)
    return hosts

def init_nodes(env, hosts, roles):
    """ Initialize nodes """
    command = ""
    for host in hostlist:
        if env == "local":
            command += ("python3 node.py -p " + host.split(":")[1] + " -r " + roles + " ")

        else:
            command += ("ssh -f " + host.split(":")[0] + " python3 $PWD/node.py -p "
                     + host.split(":")[1] + " -r" + role + " ")

    return command


def main(args):
    """ Main fuction """
    config = args.config
    print(config[1])
    #hosts = parse_hostfile(env, nodes)


def parse_args():
    """ optarg parser """
    DIE_AFTER_SECONDS_DEFAULT = 10 * 60
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--environment", required=False, type=str, default="cluster",
        help ="Default: cluster | Specify environment. Valid inputs are: (cluster | local)")

    p.add_argument("-c", "--config", required=False, type=list, default=None,
        help ="Default: None | Configuration of nodes. " +
              "Valid input is: [replicas(int), leaders(int), acceptors(int)]")

    p.add_argument("-n", "--nodes", required=False, type=int, default=8,
        help ="Default: 8 | Number of nodes to use")
    args = p.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    main(args)
