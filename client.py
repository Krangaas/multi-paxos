#!/usr/bin/env python3

import argparse
import http.client
import json
import random
import textwrap
import uuid
import time
import csv

def arg_parser():
    parser = argparse.ArgumentParser(prog="client", description="DHT client")

    parser.add_argument("nodes", type=str, nargs="+",
            help="addresses (host:port) of nodes to test")

    parser.add_argument("-i", "--iterations", required=False, type=int, default=100,
            help="Default 100 | number of test iterations")

    parser.add_argument("-s", "--store", required=False, type=int, default=0,
            help="Default 0 | if 1, write data to a file")

    parser.add_argument("-S", "--smode", required=False, type=str, default="append",
            help="Default 'append' | only used in conjuction with -s, (append|write)")

    parser.add_argument("-t", "--throughput", required=False, type=int, default=0,
        help ="Default: 0 | if 1, count throughput")
    return parser


class Lorem(object):
    """ Generates lorem ipsum placeholder text"""

    sample = """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
        tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
        veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
        commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
        velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
        cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
        est laborum.
        """

    def __init__(self):
        # Lowercase words and strip leading/trailing whitespace
        s = self.sample.lower().strip()
        # Filter out punctuation and other non-alpha non-space characters
        s = filter(lambda c: c.isalpha() or c.isspace(), s)
        # Collect filtered letters back into a string, then split into words
        s = ''.join(s).split()
        # Collapse into a set to dedupe words, then turn back into a list
        self.word_list = sorted(list(set(s)))

        self.min_words = 5
        self.max_words = 20

        self.min_sentences = 3
        self.max_sentences = 6

        self.min_paras = 1
        self.max_paras = 5

    def sentence(self):
        nwords = random.randrange(self.min_words, self.max_words)
        rand_words = [random.choice(self.word_list) for _ in range(0, nwords)]
        rand_words[0] = rand_words[0].capitalize()
        return " ".join(rand_words) + "."

    def paragraph(self):
        nsens = random.randrange(self.min_sentences, self.max_sentences)
        rand_sens = [self.sentence() for _ in range(0, nsens)]
        return textwrap.fill(" ".join(rand_sens))

    def text(self):
        nparas = random.randrange(self.min_paras, self.max_paras)
        rand_paras = [self.paragraph() for _ in range(0, nparas)]
        return "\n\n".join(rand_paras)

lorem = Lorem()


def generate_pairs(count):
    pairs = {}
    for x in range(0, count):
        key = str(uuid.uuid4())
        value = lorem.text()
        pairs[key] = value
    return pairs


def put_value(node, key, value):
    puts = 0
    start = time.time()
    conn = http.client.HTTPConnection(node)
    conn.request("PUT", "/storage/"+key, value)
    resp = conn.getresponse()

    headers = resp.getheaders()
    value = resp.read()

    contenttype = "text/plain"
    for h, hv in headers:
        if h=="Content-type":
            contenttype = hv
    if contenttype == "text/plain":
        value = value.decode("utf-8")
    conn.close()
    end = time.time()
    if throughput:
        # extract puts count
        data, puts = value.split("+")
    else:
        data = value
    tt = (end - start)
    return puts, tt


def get_value(node, key):
    gets = 0
    start = time.time()
    conn = http.client.HTTPConnection(node)
    conn.request("GET", "/storage/"+key)
    resp = conn.getresponse()

    headers = resp.getheaders()
    value = resp.read()

    contenttype = "text/plain"
    for h, hv in headers:
        if h=="Content-type":
            contenttype = hv
    if contenttype == "text/plain":
        value = value.decode("utf-8")
    conn.close()
    end = time.time()
    if throughput:
        # extract gets count
        data, gets = value.split("+")
    else:
        data = value
    tt = (end - start)
    return data, gets, tt


def get_neighbors(node):
    conn = http.client.HTTPConnection(node)
    conn.request("GET", "/neighbors")
    resp = conn.getresponse()
    if resp.status != 200:
        neighbors = []
    else:
        body = resp.read()
        neighbors = json.loads(body)
    conn.close()

    return neighbors


def walk_neighbors(start_nodes):
    to_visit = start_nodes
    visited = set()
    while to_visit:
        next_node = to_visit.pop()
        visited.add(next_node)
        neighbors = get_neighbors(next_node)
        for neighbor in neighbors:
            if neighbor not in visited:
                to_visit.append(neighbor)
    return visited


def simple_check(nodes, tries=10):
    """
    PUT/GET request on the same node, returns throughput.

    The throughput is calculated by adding the number of PUTs and GETs,
    then dividing by the total time taken between establishing the connection
    until getting a response.

    T = (GETs + PUTs)/(tGET + tPUT)
    """
    print("Simple put/get check, retreiving from same node ...")

    pairs = generate_pairs(tries)
    throughput_list = []
    successes = 0
    node_index = 0
    for key, value in pairs.items():
        try:
            puts, p_taken = put_value(nodes[node_index], key, value)
            returned, gets, g_taken = get_value(nodes[node_index], key)
            if returned == value:
                successes+=1
                if throughput:
                    # Store throughput count
                    throughput_list.append(int(gets+puts)/((g_taken+p_taken)))
        except Exception as e:
            print(e)
            pass

        node_index = (node_index+1) % len(nodes)

    success_percent = float(successes) / float(tries) * 100
    print("Stored and retrieved %d pairs of %d (%.1f%%)" % (
            successes, tries, success_percent ))
    return throughput_list


def retrieve_from_different_nodes(nodes, tries=10):
    print("Retrieving from different nodes ...")

    pairs = generate_pairs(tries)
    throughput_list = []
    successes = 0
    for key, value in pairs.items():
        try:
            puts, p_taken = put_value(random.choice(nodes), key, value)
            returned, gets, g_taken = get_value(random.choice(nodes), key)
            if returned == value:
                successes+=1
                if throughput:
                    throughput_list.append(int(gets+puts)/(g_taken+p_taken))
        except Exception as e:
            print(e)
            pass

    success_percent = float(successes) / float(tries) * 100
    print("Stored and retrieved %d pairs of %d (%.1f%%)" % (
            successes, tries, success_percent ))
    return throughput_list


def get_nonexistent_key(nodes, tries=10):
    print("Retrieving a nonexistent key ...")
    throughput_list = []
    fails = 0
    for i in range(tries):
        key = str(uuid.uuid4())
        node = random.choice(nodes)
        try:
            start = time.time()
            conn = http.client.HTTPConnection(node)
            conn.request("GET", "/storage/"+key)
            resp = conn.getresponse()

            headers = resp.getheaders()
            value = resp.read()

            contenttype = "text/plain"
            for h, hv in headers:
                if h=="Content-type":
                    contenttype = hv
            if contenttype == "text/plain":
                value = value.decode("utf-8")
            conn.close()
            end = time.time()
            if throughput:
                data, gets = value.split("+")
            if resp.status == 404:
                fails+=1
            conn.close()
            taken = end - start
            if throughput:
                throughput_list.append(int(gets)/(taken))
        except Exception as e:
            print("GET failed with exception:")
            print(e)

    fails_percent = float(fails) / float(tries) * 100
    print("Fails %d of %d (%.1f%%)" % (
            fails, tries, fails_percent ))
    return throughput_list


def store_data(dataset, mode, file, label):
    """ Store dataset """
    if mode == "w":
        data = [label, dataset]
    else:
        data = [dataset]
    with open(file, mode=mode, newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerows(data)


def main(args):
    global throughput
    throughput = args.throughput
    tries = args.iterations
    nodes = set(args.nodes)
    nodes |= walk_neighbors(args.nodes)
    nodes = list(nodes)
    print("%d nodes registered: %s" % (len(nodes), ", ".join(nodes)))

    if len(nodes)==0:
        raise RuntimeError("No nodes registered to connect to")


    print()
    simple_thr = []
    simple_thr.append(len(nodes))
    simple_thr.append(simple_check(nodes, tries))
    print()

    different_thr = []
    different_thr.append(len(nodes))
    different_thr.append(retrieve_from_different_nodes(nodes, tries))
    print()

    nonexistent_thr = []
    nonexistent_thr.append(len(nodes))
    nonexistent_thr.append(get_nonexistent_key(nodes, tries))
    print("\nClient finished testing... ")

    if args.store:
        store_data(simple_thr, args.smode, "simple.csv", ["simple_thr"])
        store_data(different_thr, args.smode, "different.csv", ["different_thr"])
        store_data(nonexistent_thr, args.smode, "nonexistent.csv", ["nonexistent_thr"])


if __name__ == "__main__":

    parser = arg_parser()
    args = parser.parse_args()
    if args.smode == "write":
        args.smode = "w"
    else:
        args.smode = "a"
    main(args)
