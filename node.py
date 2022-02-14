#!/usr/bin/env python3
import argparse
import binascii
import hashlib
import http
import json
import re
import signal
import socket
import socketserver
import threading

from http.server import BaseHTTPRequestHandler,HTTPServer

# Logger
import logging
logging.basicConfig()
logger = logging.getLogger()

# Assignment 1 node properties
object_store = {}
neighbors = []

# Assignment 2 node properties
node_name = None
node_hash = None
predecessor = None
successor = None
successor2 = None
sim_crash = False
asserted = 0
linked = 0

def hash_id(value):
    """ Hashes an input value with SHA-1 and return an ID. """
    node_hash = hashlib.sha1(value.encode())
    digest = node_hash.hexdigest()
    node_ID = int(digest, 16)
    return (node_ID) % pow(2,m_val)


class NodeHttpHandler(BaseHTTPRequestHandler):

    def send_whole_response(self, code, content, content_type="text/plain"):
        if isinstance(content, str):
            content = content.encode("utf-8")
            if not content_type:
                content_type = "text/plain"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
        elif isinstance(content, bytes):
            if not content_type:
                content_type = "application/octet-stream"
        elif isinstance(content, object):
            content = json.dumps(content, indent=2)
            content += "\n"
            content = content.encode("utf-8")
            content_type = "application/json"

        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length',len(content))
        self.end_headers()
        self.wfile.write(content)


    def extract_key_from_path(self, path):
        return re.sub(r'/storage/?(\w+)', r'\1', path)


    def key_in_range(self, a, b, c):
        """
        Check if value c is in the range (a,b] on the Chord circle using modular arithmetic.
        Args:
            a (int): Lower limit (not included in the range), the ID of the counter-clockwise neighbor
            b (int): Upper limit, the ID of this node
            c (int): Value to test, usually the key ID
        Returns:
            (bool): True if c is contained in (a,b], False otherwise.
        """
        if (a < b):
            if ((a < c) and (c <= b)):
                return True
            else:
                return False
        else:
            if ((b < c) and (c < a)):
                return False
            else:
                return True


    def do_PUT(self):
        """
        Handle a PUT request.
        If the key should be stored on this node, store it and resturn a 200 OK response.
        If the key should not be stored on this node, forward the request to clockwise neighbor.
        """
        content_length = int(self.headers.get('content-length', 0))
        value = self.rfile.read(content_length)
        key = self.extract_key_from_path(self.path)

        if sim_crash == True:
            self.send_whole_response(500, "I have sim-crashed")
            return

        if self.key_in_range(hash_id(predecessor),
                             node_hash,
                             hash_id(key)):
            # key shall be stored here
            object_store[key] = value
            # Send OK response
            if throughput:
                # count throughput
                value = ("Value stored for " + key + "+1").encode()
            else:
                value = ("Value stored for " + key).encode()
            self.send_whole_response(200, value)
        else:
            # The key shall not be stored on this node.
            # Forward the request to next neighbor
            conn = http.client.HTTPConnection(successor)
            conn.request("PUT", "/storage/"+key, value)
            resp = conn.getresponse()
            value = resp.read()
            conn.close()
            if resp.status == 500:
                # successor has crashed
                self.reestablish_successor()
                # The key shall not be stored on this node.
                # Forward the request to next neighbor
                conn = http.client.HTTPConnection(successor)
                conn.request("PUT", "/storage/"+key, value)
                resp = conn.getresponse()
                value = resp.read()
                conn.close()

            if throughput:
                # exctract and increment throughput counter
                value = value.decode()
                data, gets = value.split("+")
                gets = str(int(gets)+1)
                value = data + "+" + gets
                value = value.encode()

            if resp.status != 200:
                self.send_whole_response(404, value)
            else:
                # Send OK response
                self.send_whole_response(200, value)


    def reestablish_successor(self):
        """ Reestablish connection to a successor. """
        global successor
        global successor2
        global neighbors
        # request next neighbors node info
        conn = http.client.HTTPConnection(successor2)
        conn.request("GET", "/node-info")
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            # Two successive nodes have crashed,
            # with the current implementation the network can not fully recover
            # (unless one of the two nodes manage to recover)
            # TODO: Add fingertable!
            self.send_whole_response(resp.status, resp.read())
            return
        value = resp.read()
        value = json.loads(value)

        # set next next neighbor as next
        successor = successor2
        neighbors[1] = successor2
        # link up with next next neighbor
        if value["successor"] != node_name:
            successor2 = value["successor"]
            neighbors[2] = value["successor"]
        else:
            # in a 2-node network
            successor2 = None
            neighbors[2] = None

        # request next neighbor to link up with this node
        conn = http.client.HTTPConnection(successor)
        conn.request("POST", "/link/prev/"+node_name)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            self.send_whole_response(resp.status, resp.read())


    def do_GET(self):
        """ Handle a GET request. """
        if sim_crash == True:
            self.send_whole_response(500, "I have sim-crashed")
        elif self.path.startswith("/storage"):
            self.store()
        elif self.path.startswith("/neighbors"):
            self.send_whole_response(200, neighbors)
        elif self.path.startswith("/node-info"):
            self.node_info()
        else:
            self.send_whole_response(404, "Unknown path: " + self.path)


    def node_info(self):
        """
        Handle a /node-info GET request.
        Sends a JSON response object with information about this node.
        """
        node_info = {
                "node_hash": node_hash,
                "successor": successor,
                "others": [predecessor, successor2],
                }
        node_info_json = json.dumps(node_info, indent=2)
        self.send_whole_response(200, node_info_json, content_type="application/json")


    def store(self):
        """
        Handle a /storage GET request.
        If the key is not stored on this node then forward the request to clockwise neighbor.
        If the key is stored on this node, return a 200 OK response with the stored value.
        If the key should be stored on this node but does not exist, return a 404 response.
        """
        key = self.extract_key_from_path(self.path)

        if self.key_in_range(hash_id(predecessor),
                             node_hash,
                             hash_id(key)):
            try:
                if throughput:
                    # increment throughput counter
                    value = object_store[key]+b'+1'
                else:
                    value = object_store[key]
                self.send_whole_response(200, value)
            except:
                # key does not exist in network, as it was supposed to be here
                if throughput:
                    # increment throughput counter
                    value = ("No object with key " + key + " on this node+1").encode()
                else:
                    value = ("No object with key " + key + " on this node").encode()
                self.send_whole_response(404, value)
        else:
            # key is not stored here,
            # forward request to next neighbor
            conn = http.client.HTTPConnection(successor)
            conn.request("GET", "/storage/"+key)
            resp = conn.getresponse()
            value = resp.read()

            if resp.status == 500:
                # successor has crashed
                self.reestablish_successor()
                # key is not stored here,
                # forward request to next neighbor
                conn = http.client.HTTPConnection(successor)
                conn.request("GET", "/storage/"+key)
                resp = conn.getresponse()
                value = resp.read()

            if throughput:
                # exctract and increment throughput counter
                value = value.decode()
                data, gets = value.split("+")
                gets = str(int(gets)+1)
                value = data + "+" + gets
                value = value.encode()

            if resp.status != 200:
                self.send_whole_response(resp.status, value)
            else:
                self.send_whole_response(200, value)


    def do_POST(self):
        """ Handle a POST request. """
        global sim_crash
        global linked

        if self.path == "/sim-recover":
            sim_crash = False
            self.join(internal=True)
            #self.send_whole_response(200, "")

        elif self.path == "/sim-crash":
            sim_crash = True
            linked = 0
            self.send_whole_response(200, "")

        elif sim_crash == True:
            self.send_whole_response(500, "I have sim-crashed")

        elif self.path.startswith("/assert-network"):
            self.assert_network()

        elif self.path == "/leave":
            self.leave()

        elif self.path.startswith("/join"):
            self.join()

        elif self.path.startswith("/link"):
            self.link()

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)


    def assert_network(self):
        """
        Assert that network is fully functional.
        Walk the whole network, reestablishing connections where neccesary.
        """
        origin = self.path.split("/")[-1:][0]

        if origin == successor:
            self.send_whole_response(200, "Network successfully asserted.")
            return

        conn = http.client.HTTPConnection(successor)
        conn.request("GET", "/node-info")
        resp = conn.getresponse()
        conn.close()
        if resp.status == 500:
            # successor has crashed
            self.reestablish_successor()
            conn = http.client.HTTPConnection(successor)
            conn.request("GET", "/node-info")
            resp = conn.getresponse()
            conn.close()

        if resp.status == 200:
            conn = http.client.HTTPConnection(successor)
            conn.request("POST", "/assert-network/"+origin)
            assert_resp = conn.getresponse()
            value = assert_resp.read()
            conn.close()

        else:
            self.send_whole_response(501, "Handling of successive nodes crashing not implemented.")
            return

        if assert_resp.status == 500:
            self.send_whole_response(501, "Handling of successive nodes crashing not implemented.")
            return
        else:
            self.send_whole_response(assert_resp.status, value)


    def leave(self):
        """
        Handle a POST /leave request.
        Link up this nodes next and previous neighbors and previous to nexts next.
        Then transfer keys to this nodes next.
        Finally, establish a single-node network consisting of this node.
        """
        global successor
        global predecessor
        global successor2
        global neighbors
        global linked

        if successor == node_name or predecessor == node_name or linked == 0:
            # node is already in a single-node network
            self.send_whole_response(200, "Ok, "+node_name+" already in single-node network")
            return

        # request next neighbor to link up with previous neighbor
        conn = http.client.HTTPConnection(successor)
        conn.request("POST", "/link/prev/"+predecessor)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            self.send_whole_response(resp.status, resp.read())
            return

        # request previous neighbor to link up with next neighbor
        conn = http.client.HTTPConnection(predecessor)
        conn.request("POST", "/link/next/"+successor)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            # network is most likely borked if this happens,
            # as successor has already linked up with predecessor
            # TODO: Unbork network(?)
            self.send_whole_response(resp.status, resp.read())
            return

        # request previous neighbor to link up with next neighbors next
        conn = http.client.HTTPConnection(predecessor)
        conn.request("POST", "/link/nextnext/"+successor2)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            self.send_whole_response(resp.status, resp.read())
            return

        # transfer keys to successor
        for pair in object_store.items():
            conn = http.client.HTTPConnection(successor)
            conn.request("PUT", "/storage/"+pair[0], pair[1])
            resp = conn.getresponse()
            conn.close()
            if resp.status != 200:
                # Failed to transfer key-value pair
                # TODO: Try again?
                self.send_whole_response(resp.status, resp.read())
                return

        # unlink from all neighbors
        successor = node_name
        neighbors[1] = node_name
        predecessor = node_name
        neighbors[0] = node_name
        successor2 = node_name
        neighbors[2] = node_name
        linked = 0
        self.send_whole_response(200, "Ok")


    def join(self, internal=False):
        """
        Handle a POST /join request.
        Connect with nodes in network in turn and find correct position on the circle,
        starting with nprime.
        When the correct position is found, establish links with the found
        successor and predecessor
        """
        global successor
        global predecessor
        global successor2
        global neighbors
        global linked
        found_pos = 0

        if internal == False:
            nprime = re.sub(r'^/join\?nprime=([\w:-]+)$', r'\1', self.path)
        else:
            # node is attempting to join network after recovering from a crash
            nprime = successor

        if linked:
            # node is already in a network, no need to join again
            self.send_whole_response(200, "Ok, already in the network.")
            return

        # if node is not linked and request is sent to link up to itself, send 200 Ok
        if node_name == nprime:
            linked = 0
            self.send_whole_response(200, "Ok, "+ node_name+" already in single network")
            return

        while not found_pos:
            conn = http.client.HTTPConnection(nprime)
            conn.request("GET", "/node-info")
            resp = conn.getresponse()
            conn.close()
            if resp.status == 200:
                value = resp.read()
                value = json.loads(value)

                pre = value["others"][0]      #requested node predecessor

                suc_hash = value["node_hash"] #requested node hash
                pre_hash = hash_id(pre)       #requested node predecessor hash
                if suc_hash == pre_hash:
                    # joining a single-node network
                    found_pos = 1
                elif self.key_in_range(pre_hash, suc_hash, node_hash):
                    # found correct position in network
                    found_pos = 1
                else:
                    nprime = value["successor"]
            elif resp.status == 500:
                self.send_whole_response(500, "Unable to connect to network.")
                return
        # link up joining node to network
        successor = nprime
        neighbors[1] = nprime
        predecessor = pre
        neighbors[0] = pre
        successor2 = value["successor"]
        neighbors[2] = value["successor"]

        # OPTIONAL: retrieve key-value pairs from successor that belong here

        # link up next and previous with joining node
        # request next neighbor to link up with this node
        conn = http.client.HTTPConnection(successor)
        conn.request("POST", "/link/prev/"+node_name)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            self.send_whole_response(resp.status, resp.read())

        # request previous neighbor to link up with this node
        conn = http.client.HTTPConnection(predecessor)
        conn.request("POST", "/link/next/"+node_name)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            self.send_whole_response(resp.status, resp.read())

        # request previous neighbor to link up with next node
        conn = http.client.HTTPConnection(predecessor)
        conn.request("POST", "/link/nextnext/"+successor)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            self.send_whole_response(resp.status, resp.read())

        linked = 1
        self.send_whole_response(200, "Ok "+ node_name + " linked up with "+successor+" "+predecessor)


    def link(self):
        """
        Handle a POST /link request.
        Update this nodes previous, next, or next next neighbor.
        """
        global predecessor
        global successor
        global successor2
        global neighbors
        global linked
        cmd, node = self.path.split("/")[-2:]
        if cmd == "prev":
            predecessor = node
            neighbors[0] = node
        elif cmd == "next":
            successor = node
            neighbors[1] = node
        elif cmd == "nextnext":
            successor2 = node
            neighbors[2] = node
        else:
            # bad command (not prev or next)
            self.send_whole_response(404, "Unknown path: " + self.path)


        if node_name == successor or node_name == predecessor:
            linked = 0
        else:
            linked = 1
        self.send_whole_response(200, "Ok")


def arg_parser():
    PORT_DEFAULT = 8000
    DIE_AFTER_SECONDS_DEFAULT = 10 * 60
    parser = argparse.ArgumentParser(prog="node", description="DHT Node")

    parser.add_argument("-p", "--port", type=int, default=PORT_DEFAULT,
            help="port number to listen on, default %d" % PORT_DEFAULT)

    parser.add_argument("--die-after-seconds", type=float,
            default=DIE_AFTER_SECONDS_DEFAULT,
            help="kill server after so many seconds have elapsed, " +
                "in case we forget or fail to kill it, " +
                "default %d (%d minutes)" % (DIE_AFTER_SECONDS_DEFAULT, DIE_AFTER_SECONDS_DEFAULT/60))

    parser.add_argument("-m", "--mbits", type=int, default=6,
            help ="Default: 6 | Number of bits m for computing identifier (2^m)")

    parser.add_argument("neighbors", type=str, nargs="*",
            help="addresses (host:port) of neighbor nodes (must be at least three addresses)")

    parser.add_argument("-t", "--throughput", required=False, type=int, default=0,
        help ="Default: 0 | if 1, count throughput")
    return parser


class ThreadingHttpServer(HTTPServer, socketserver.ThreadingMixIn):
    pass


def run_server(args):
    global server      # server object
    global neighbors   # list of neighbors
    global m_val       # mbits value
    global throughput  # throughput flag
    global node_name   # name of node
    global node_hash   # hash of node name
    global successor   # next node in network
    global successor2  # next next node in network
    global predecessor # previous node in network
    global sim_crash   # crash flag
    global linked      # link flag

    neighbors = args.neighbors
    m_val = args.mbits
    throughput = args.throughput
    server = ThreadingHttpServer(('', args.port), NodeHttpHandler)
    node_name = "{}:{}".format(socket.gethostname().replace(".local",""), args.port)
    node_hash = hash_id(node_name)
    logger = logging.getLogger(node_name)
    logger.setLevel(logging.INFO)

    if len(args.neighbors) == 0:
        successor = node_name
        predecessor = node_name
        successor2 = node_name

    if len(args.neighbors) >= 1:
        successor = args.neighbors[1]
        predecessor = args.neighbors[0]
        successor2 = args.neighbors[2]
        if successor2 == node_name or successor2 == successor:
            successor2 = predecessor
            args.neighbors[2] = predecessor


    if node_name != successor:
        linked = 1

    neighbors = args.neighbors

    def server_main():
        print("Starting server on port {}. neighbors: {}. linked {}".format(args.port, args.neighbors, linked))
        server.serve_forever()
        print("Server has shut down")

    def shutdown_server_on_signal(signum, frame):
        print("We get signal (%s). Asking server to shut down" % signum)
        server.shutdown()

    # Start server in a new thread, because server HTTPServer.serve_forever()
    # and HTTPServer.shutdown() must be called from separate threads
    thread = threading.Thread(target=server_main)
    thread.daemon = True
    thread.start()

    # Shut down on kill (SIGTERM) and Ctrl-C (SIGINT)
    signal.signal(signal.SIGTERM, shutdown_server_on_signal)
    signal.signal(signal.SIGINT, shutdown_server_on_signal)

    # Wait on server thread, until timeout has elapsed
    #
    # Note: The timeout parameter here is also important for catching OS
    # signals, so do not remove it.
    #
    # Having a timeout to check for keeps the waiting thread active enough to
    # check for signals too. Without it, the waiting thread will block so
    # completely that it won't respond to Ctrl-C or SIGTERM. You'll only be
    # able to kill it with kill -9.
    thread.join(args.die_after_seconds)
    if thread.is_alive():
        print("Reached %.3f second timeout. Asking server to shut down" % args.die_after_seconds)
        server.shutdown()

    print("Exited cleanly")

if __name__ == "__main__":

    parser = arg_parser()
    args = parser.parse_args()
    run_server(args)
