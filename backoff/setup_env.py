import argparse, os


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

    return hosts

def main(args):
    """ Main """
    if args.environment == "cluster":
        print("Running on several machines not supported (yet).")
        exit(0)
    if test == None:
        os.system("python3 env.py -f " + str(args.fails) + " -r " + str(args.requests)
                  + " -c " + str(args.configs) + "-C " + str(args.clients))


def parse_args():
    """ optarg parser """
    DIE_AFTER_SECONDS_DEFAULT = 10 * 60
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--environment", required=False, type=str, default="local",
        help = "Default: cluster | Specify environment. " +
               "Valid inputs are: (cluster | local)")

    p.add_argument("-f", "--fails", required=False, type=int, default=1,
        help = "Default: 1 | Number of acceptable fails.")

    p.add_argument("-r", "--requests", required=False, type=int, default=40,
        help = "Default: 40 | Number of requests to send.")

    p.add_argument("-c", "--configs", required=False, type=int, default=1,
        help = "Default: 1 | Number of role configurations to try.")

    p.add_argument("-C", "--clients", required=False, type=int, default=1,
        help = "Default: 1 | Number of clients.")

    p.add_argument("-R", "--roles", required=False, type=list, default=[2,2,3],
        help = "Default: 223 | Configuration of roles. " +
               "Valid input is: [NREPLICAS][NLEADERS][NACCEPTORS]")

    p.add_argument("-t", "--test", required=False, type=str, default=None,
        help = "Default: None | Specify which test to run. " +
               "Valid inputs are: (throughput | ...)")
    args = p.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    main(args)
