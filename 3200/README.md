Evaluation code for INF-3203 Assignment 1
==================================================
Some examples:
--------------------------------------------------
The following sequence of commands will initialize the network on the cluster with 50 nodes,
then perform growing and shrinking tests. The nodes will terminate after two minutes:
```
        python3 init_nodes.py -n 50 --die-after-seconds 120
        python3 evaluate_network.py -g 1 -s 1
```

The following sequence of commands will initialize the network on the cluster with 50 nodes,
then perform a test that crashes nodes in bursts. The nodes will terminate after two minutes:
```
        python3 init_nodes.py -n 50 --die-after-seconds 120
        python3 evaluate_network.py -b 1
```
**NOTE**: Both command sequences presented above must be run on the cluster, they will fail if they are run locally.

The following sequence of commands will initialize the network locally with 10 nodes,
then the attempt to sequentially crash up to a third of the nodes on the network. The nodes will terminate after two minutes:
```
        python3 init_nodes.py -e local -n 50 --die-after-seconds 120
        python3 evaluate_network.py -c 1
```
**NOTE**: For this sequence it might be neccessary to run each command in different terminals, as they are run locally.



Evaluation tests: `evaluate_network.py`
--------------------------------------------------

This is a unit test script that will perform various evaluation tests depending on input parameters. The test cases can be run in combinations, but the clearest results are achieved by running each test case by itself, then resetting the network.

The script has the following input arguments:
- settle-ms (\-\-sette\-ms): After a join/leave call, wait for the network to settle.
- growtest (\-g|\-\-growtest): If 1, perform tests that grow the network.
- shrinktest (\-s|\-\-shrinktest): If 1, perform tests that shrink the network to half its size.
- crashtest (\-c|\-\-crashtest): If 1, perform tests that crashes and recovers nodes one at a time.
- bursttest (\-b|\-\-bursttest): If 1, perform tests that crashes nodes in increasing bursts.
- help (\-\-help): Display help text and exit

to use:
1. Start your network
2. Run the evaluation code with at least one test case enabled.
Example:
```
        python3 evaluate_network.py -g 1
```
This command will perform growing tests on the network.



Test client: `init_nodes.py`
--------------------------------------------------
Code to initialize the network.

It has the following input parameters:
- environment (-e|\-\-env): Specify environment. Valid inputs are: (cluster | local)
- mbits (-m|\-\-mbits): Number of bits m for computing identifier (2^m) (int)
- nodes (-n|\-\-nodes): Number of nodes to use (int)
- throughput (-t|\-\-throughput): If 1 enable *count throughput mode*. Nodes will append the throughput to response messages.
- debug (-D|\-\-debug): If 1, print resultant terminal commands and exit (int)
- singlemode (-s|\-\-singlemode): If 1, initiate all nodes as a single-node network (int)
- help (\-\-help): Display help text and exit

Examples:
```
        python3 init_nodes.py -e local -n 8
```
This command will initalize the network locally with 8 nodes.
```
        python3 init_nodes.py -n 50
```
This command will initalize the network on the cluster with 50 nodes.
**NOTE:** This command must be run on the cluster, it will fail if it is run locally.



node: `node.py`
--------------------------------------------------
This is code for a node.

It has the following input parameters:
- port (-p|\-\-port): port number to listen on. (int)
- die-after-seconds (--die-after-seconds): Kills the node after so many seconds have elapsed. (float)
- mbits (-m|\-\-mbits): Number of bits m for computing identifier (2^m) (int)
- neighbors: addresses (host:port) of neighbour nodes (must be at least three addresses)
- throughput (-t|\-\-throughput): If 1 enable *count throughput mode*. Nodes will append the throughput to response messages.
- help (\-\-help): Display help text and exit

Example:
```
    python3 node.py -p 8000 localhost:8001 localhost:8002
```



Calculate standard deviation and mean: `calc_std_mean.py`
--------------------------------------------------
This script will calculate the standard deviation and the mean for two datasets, then plot the results. It has no input arguments.
Example:
```
    python3 calc_std_mean.py
```



Test client: `client.py`
--------------------------------------------------

This is a simple Python script to check a node's API.

The client will walk the network using the `/neighbours` call, and then it will
perform a few simple checks to see if it can PUT and GET values using the
`/storage/<KEY>` call. Depending on input parameters, the client will then store resulting data from the tests to specific files.

The script has the following input arguments:
- nodes (-n|\-\-nodes): Starting node, this is the node that the client will connect to (host:port)
- iterations (-i|\-\-iterations): Number of key and value pairs that will populate the network (int)
- store (-s|\-\-store): If 1, store resulting datasets (int)
- smode (-S|\-\-smode): Writing mode, only used in conjunction with -s. (append|write)
- throughput (-t|\-\-throughput): If 1 enable *count throughput mode*, only used if the nodes have also been initialized in this mode (int)
- help (\-\-help): Display help text and exit

to use:
1. Start your network
2. Run the client code, giving it a node host:port to start with.
Example:
```
        python3 client.py localhost:8000
```



Plot data: `plot_data.py`
--------------------------------------------------
Plots output data from from given input file.

It has one input parameter:
- file: A CSV file in the following format:
    <name of the dataset>
    <number of nodes>, <stringified list of datapoints>
    <number of nodes>, <stringified list of datapoints>
    ...

Running the script *client.py* with writing mode enabled will produce three files (simple.csv, different.csv, nonexistent.csv) in the appropriate format.
For each dataset the code will plot its average value and its standard deviation

Example:
```
        python3 plot_data.py simple.csv
```



Example Code for INF-3200, Assignment 2
=====================================================

This repository contains example code and test utilities for Assignment 2.

- `dummy_node.py` ---
    A skeleton node that superficially implements the required API, but has no
    actual functionality.

- `api_check.py` ---
    A set of superficial API tests to check that they respond with the correct formats.
    The dummy node passes these tests.

Example usage
--------------------------------------------------

From the bash command line:

```bash
# Start nodes in background
./dummy_node.py --port 50001 &
./dummy_node.py --port 50002 &

# Run API check
./api_check.py $HOSTNAME:50001 $HOSTNAME:5002

# Kill nodes
pkill -f dummy_node.py
```
