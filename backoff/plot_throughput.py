#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import csv
import sys
import random
plt.rcParams['axes.linewidth'] = 0.1

def parse_data(n):
    """ Parse data stored in replica files """
    val_store = {}
    for i in range(0, int(n)):
        with open("thr_replica_"+str(i), mode='r') as f:
            for line in f:
                if line.startswith('clients'):
                    clients = line.split('|')[0].split(':')[1]
                    if i == 0:
                        val_store[clients] = []
                else:
                    value = line.rstrip('\n').split(': ')[1]
                    val_store[clients].append(float(value))
    return val_store


def create_plot(labels, avgs, stds, title):
    """ Create and show plot """
    fig = plt.figure()
    plt.errorbar(labels,
                 avgs,
                 yerr=stds,
                 label="plot",
                 linestyle='None',
                 marker='.',
                 capsize=5)
    plt.title(title)
    plt.ylabel("Throughput (secs)")
    plt.xlabel("Number of clients")
    plt.show()


def main():
    try:
        n = sys.argv[1]
    except:
        print("Please specify number of replicas. Example: Python3 plot_throughput.py NREPLICAS TITLE")
        exit(0)
    try:
        title = sys.argv[2]
    except:
        print("Please specify plot title. Example: Python3 plot_throughput.py NREPLICAS TITLE")
        exit(0)
    data = parse_data(n)

    label = []
    avgs = []
    stds = []

    for clients in data.keys():
        label.append(clients)

    for d in data:
        av = np.mean(data[d])
        avgs.append(av)

        std = np.std(data[d])
        stds.append(std)

    create_plot(label, avgs, stds, title)

if __name__ == "__main__":
    main()
