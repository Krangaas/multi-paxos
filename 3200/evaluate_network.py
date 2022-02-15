#!/usr/bin/env python3

import argparse
import json
import random
import threading
import string
import time
import unittest
import uuid
import random
import math
import time
import socket

from client import walk_neighbors, get_neighbors

# Logger
import logging
logging.basicConfig()
logger = logging.getLogger()

# Python version check
import sys

if sys.version_info[0] <= 2:
    import httplib
    import urlparse

elif sys.version_info[0] >= 3:
    import http.client as httplib

else:
    logger.warn("Unexpected Python version", sys.version_info())

# Global variables set from options and used in unit tests
# (since it's hard to parameterize tests in Python 2)

SETTLE_MS_DEFAULT = 20
settle_ms = SETTLE_MS_DEFAULT

test_nodes = []

def reset_network(state):
    """ Link or unlik all nodes in the network """
    prevnode = test_nodes[0]
    for node in test_nodes:
        if state == "single":
            # Make node not part of the network
            r = do_request(node, "POST", "/leave")
            time.sleep(settle_ms / 2000.0)
        elif state == "linked":
            # Join one node to the other
            r = do_request(node, "POST", "/join?nprime="+prevnode)
            time.sleep(settle_ms / 2000.0)
            prevnode = node
        else:
            print("\nState must be either 'linked' or 'single'")
            exit(0)


def read_hostfile():
    with open('hostfile', mode='r') as f:
        for line in f:
            node = line.splitlines()[0]
            test_nodes.append(node)


def set_test_nodes(nodes):
    global test_nodes
    test_nodes = nodes


def parse_args():
    parser = argparse.ArgumentParser(prog="evaluate_network", description="Network evaluator")

    parser.add_argument("--settle-ms", type=int,
            default=SETTLE_MS_DEFAULT,
            help="After a join/leave call, wait for the network to settle (default {} ms)"
                .format(SETTLE_MS_DEFAULT))
    parser.add_argument("-g", "--growtest", required=False, default=0,
                        help="Default: 0 | if 1, do grow network test")
    parser.add_argument("-s", "--shrinktest", required=False, default=0,
                        help="Default: 0 | if 1, do shrink network test")
    parser.add_argument("-c", "--crashtest", required=False, default=0,
                        help="Default: 0 | if 1, do crash network test")
    parser.add_argument("-b", "--bursttest", required=False, default=0,
                        help="Default: 0 | if 1, do nurst crash network test")

    return parser.parse_args()


def describe_exception(e):
    return "%s: %s" % (type(e).__name__, e)


class Response(object): pass


def search_header_tuple(headers, header_name):
    if sys.version_info[0] <= 2:
        header_name = header_name.lower()
    elif sys.version_info[0] >= 3:
        pass

    for key, value in headers:
        if key == header_name:
            return value
    return None


def do_request(host_port, method, url, body=None, accept_statuses=[200], timeout=None):
    def describe_request():
        return "%s %s%s" % (method, host_port, url)

    conn = None
    try:
        if not timeout:
            conn = httplib.HTTPConnection(host_port)
        else:
            conn = httplib.HTTPConnection(host_port, timeout=timeout)

        try:
            conn.request(method, url, body)
            r = conn.getresponse()
        except socket.timeout as st:
            return("Request timed out")
        except Exception as e:
            raise Exception(describe_request()
                    + " --- "
                    + describe_exception(e))

        status = r.status
        if status not in accept_statuses:
            raise Exception(describe_request() + " --- unexpected status %d" % (r.status))

        headers = r.getheaders()
        body = r.read()

    finally:
        if conn:
            conn.close()

    content_type = search_header_tuple(headers, "Content-type")
    if content_type == "application/json":
        try:
            body = json.loads(body)
        except Exception as e:
            raise Exception(describe_request()
                    + " --- "
                    + describe_exception(e)
                    + " --- Body start: "
                    + body[:30])

    if content_type == "text/plain" and sys.version_info[0] >= 3:
        body = body.decode()

    r2 = Response()
    r2.status = status
    r2.headers = headers
    r2.body = body

    return r2


class GrowNetwork(unittest.TestCase):
    """ Test to grow a network from single nodes. """
    def setUp(self):
        if len(test_nodes) < 1:
            raise unittest.SkipTest("Need at least one node")
        reset_network("single")


    def test_assert_single_node_networks(self):
        print("\nAsserting single-node networks...")
        for node in test_nodes:
            r = do_request(node, "GET", "/node-info")
            time.sleep(settle_ms / 1000.0)
            # In a single-node network, the node should be its own successor
            self.assertEqual(r.body["successor"], node)
            self.assertEqual(r.body["others"][0], node)


    def test_grow_network(self):
        print("\nGrowing network...")
        prevnode = test_nodes[0]
        start = time.time()
        for node in test_nodes:

            # Join one node to the other
            r = do_request(node, "POST", "/join?nprime="+prevnode)
            time.sleep(settle_ms / 1000.0)
            self.assertEqual(r.status, 200)
            prevnode = node

            # skip asserting for first node, as it is the only one in the "network"
            if node != prevnode:
                r = do_request(node, "GET", "/node-info")
                time.sleep(settle_ms / 1000.0)
                # Assert that node is not in a single-node network
                self.assertNotEqual(r.body["successor"], node)
                self.assertNotEqual(r.body["others"][0], node)
        end = time.time()
        print("No. of nodes:", len(test_nodes), "| Time taken (secs):",end-start)


class ShrinkNetwork(unittest.TestCase):
    def setUp(self):
        if len(test_nodes) < 1:
            raise unittest.SkipTest("Need at least one nodes")
        reset_network("linked")


    def test_assert_linked_network(self):
        print("\nAsserting linked-node network...")
        for node in test_nodes:
            r = do_request(node, "GET", "/node-info")
            time.sleep(settle_ms / 1000.0)
            # nodes should not be linked to themselves
            self.assertNotEqual(r.body["successor"], node)
            self.assertNotEqual(r.body["others"][0], node)


    def test_shrink_network(self):
        print("\nShrink network...")
        leaves = 0
        left = []
        start = time.time()
        for node in test_nodes:
            if leaves >= len(test_nodes)/2:
                break
            # Make node not part of the network
            r = do_request(node, "POST", "/leave")
            time.sleep(settle_ms / 1000.0)
            self.assertEqual(r.status, 200)
            leaves += 1

            left.append(node)
            # Assert that node is in a single-node network
            r = do_request(node, "GET", "/node-info")
            time.sleep(settle_ms / 1000.0)
            self.assertEqual(r.body["successor"], node)
            self.assertEqual(r.body["others"][0], node)
            self.assertEqual(r.body["others"][1], node)
        end = time.time()
        #regrow the network
        print("Regrow network...")
        for node in left:
            r = do_request(node, "POST", "/join?nprime="+test_nodes[-1])
            time.sleep(settle_ms / 1000.0)
            self.assertEqual(r.status, 200)

        print("No. of nodes:", len(test_nodes), "| Time taken (secs):",end-start)


class NodeCrash(unittest.TestCase):
    def setUp(self):
        if len(test_nodes) < 50:
            raise unittest.SkipTest("Need at least 50 nodes")
        reset_network("linked")


    def test_assert_network_crashed_node(self):
        print("\nCrash one node and assert network stability...")
        crash_node = test_nodes[random.randint(0,len(test_nodes)-1)]
        # Assert that node is up
        r = do_request(crash_node, "GET", "/node-info")
        time.sleep(settle_ms / 1000.0)
        self.assertEqual(r.status, 200)
        assert_node = r.body["others"][1]

        # sim-crash one node
        r = do_request(crash_node, "POST", "/sim-crash")
        time.sleep(settle_ms / 1000.0)

        # Assert that node has sim-crashed
        r = do_request(crash_node, "GET", "/node-info",
                       accept_statuses=[500])
        time.sleep(settle_ms / 1000.0)
        self.assertEqual(r.status, 500)

        # assert network stability despite crashed node
        r = do_request(assert_node, "POST", "/assert-network/"+assert_node)
        self.assertEqual(r.status, 200)

        r = do_request(crash_node, "POST", "/sim-recover")
        time.sleep(settle_ms / 1000.0)

        # Assert that node has sim-recovered
        print("Assert network stability after recovery...")
        r = do_request(crash_node, "GET", "/node-info")
        time.sleep(settle_ms / 1000.0)
        self.assertEqual(r.status, 200)

        # assert network stability after recovery
        r = do_request(assert_node, "POST", "/assert-network/"+assert_node)
        time.sleep(settle_ms / 1000.0)
        self.assertEqual(r.status, 200)


    def test_assert_network_several_crashed_nodes(self):
        print("\nCrash several nodes and assert network stability...")
        crashed = [] # list of all attempted crashed nodes
        crashes = 0 # number of crashed nodes
        recoveries = 0 # number of successful recoveries
        # crash up to a third of the total amount of nodes, rounded up
        k = int(math.ceil(len(test_nodes)/3))
        for i in range(k):
            print("Crash", i+1,"node(s)")
            crash_node = None

            # find a node that has not been crashed yet
            while not crash_node:
                index = random.randint(0,len(test_nodes)-1)
                if test_nodes[index] not in crashed:
                    crash_node = test_nodes[index]
                    crashed.append(crash_node)

            # Assert that node is up
            r = do_request(crash_node, "GET", "/node-info")
            time.sleep(settle_ms / 1000.0)
            self.assertEqual(r.status, 200)
            assert_node = r.body["others"][1]

            # sim-crash one node
            r = do_request(crash_node, "POST", "/sim-crash")
            time.sleep(settle_ms / 1000.0)
            self.assertEqual(r.status, 200)

            # assert network stability despite crashed node
            r = do_request(assert_node, "POST", "/assert-network/"+assert_node,
                           accept_statuses=[200,500,501], timeout=60)
            if r.status == 501 or r.status == 500:
                break
            else:
                crashes += 1

        print("Attempt to recover nodes...")
        for node in crashed:
            r = do_request(node, "POST", "/sim-recover", accept_statuses=[200,500], timeout=60)
            if r == "Request timed out":
                print("Request timed out")
                break
            time.sleep(settle_ms / 1000.0)
            if r.status == 200:
                recoveries += 1

        print("Managed to successfully stabilize with", crashes, "crashed nodes before failing")
        print("Managed to successfully recover", recoveries, "nodes")


class NodeCrashBurst(unittest.TestCase):
    def setUp(self):
        if len(test_nodes) < 50:
            raise unittest.SkipTest("Need at least 50 nodes")
        reset_network("linked")


    def test_assert_network_burst_crashed_nodes(self):
        print("\nCrash several nodes and assert network stability...")
        crashes = 0
        recoveries = 0

        crashed = [] # list of all crashed nodes
        burst_iter = 0 # burst crash iterator
        unrecoverable = False # network recover flag

        # node that recieves assertion request
        assert_node = test_nodes[random.randint(0,len(test_nodes)-1)]

        while unrecoverable == False:
            # initialize list of nodes to be crashed as empty each iteration
            crashed_nodes_this_iter = []

            # populate array of nodes to be crashed
            while len(crashed_nodes_this_iter) < burst_iter+1:
                index = random.randint(0,len(test_nodes)-1)

                if test_nodes[index] not in crashed and test_nodes[index] != assert_node:
                    crashed_nodes_this_iter.append(test_nodes[index])
                    crashed.append(test_nodes[index])

            # sim crash all nodes for this burst iteration
            for node in crashed_nodes_this_iter:
                r = do_request(node, "POST", "/sim-crash")
                time.sleep(settle_ms / 1000.0)
                self.assertEqual(r.status, 200)

            # assert network stability after nodes have crashed
            r = do_request(assert_node, "POST", "/assert-network/"+assert_node,
                           accept_statuses=[200,500,501], timeout=60)
            if r == "Request timed out":
                unrecoverable = True
            elif r.status == 501 or r.status == 500:
                unrecoverable = True
            else:
                burst_iter += 1

        print("Managed to successfully stabilize with crash burst:", burst_iter)


if __name__ == "__main__":

    args = parse_args()

    settle_ms = args.settle_ms
    read_hostfile()
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()

    if args.growtest:
        test_suite.addTests(test_loader.loadTestsFromTestCase(GrowNetwork))
    if args.shrinktest:
        test_suite.addTests(test_loader.loadTestsFromTestCase(ShrinkNetwork))
    if args.crashtest:
        test_suite.addTests(test_loader.loadTestsFromTestCase(NodeCrash))
    if args.bursttest:
        test_suite.addTests(test_loader.loadTestsFromTestCase(NodeCrashBurst))

    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)
