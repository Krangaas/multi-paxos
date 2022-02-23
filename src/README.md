INF-3203 Assignment 1
==================================================
The following command will display the help text for the test script that handles all interaction with the multi-paxos implementation and exit.
```
        python3 run_tests.py -h
```

The following command will perform a single run of the multi-paxos protocol with the default role configuration (2 replicas, 2 leaders, 3 acceptors), 3 clients and 100 total requests.
Then the program will assert that the replicas reached a consensus with respect to the sequence of operations to perform.
```
        python3 run_tests.py -t simple_test -c 3 -r 100
```

The following command will perform a sequence of 13 tests where the number of leaders are incremented by 5 for each run. The role configuration will initially be 2 replicas, 1 leader and 3 acceptors. 6 clients will be simulated for each run which will send a total of 30 requests.
```
        python3 run_tests.py -t leaders -C2,1,3 -c 6 -r 30 -n 13 -i 5
```

The following command will perform a single run of the multi-paxos protocol and assert that consensus was reached. The role configuration gets set based on the minimum allowed failing processes (5) for each role.
```
        python3 run_tests.py -t simple_test -f 5
```
