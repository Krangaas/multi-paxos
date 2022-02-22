#!/usr/bin/env python3
from cProfile import label
import numpy as np
import matplotlib.pyplot as plt
import sys
plt.rcParams['axes.linewidth'] = 0.1

def parse_data(n, increment, start):
    """ Parse data stored in n replica files """
    data = {}
    for i in range(0, int(n)):
        entry = start - increment
        with open("thr_replica_"+str(i), mode='r') as f:
            for line in f:
                if line.startswith('clients'):
                    entry += increment
                    if entry not in data.keys():
                        data[entry] = []
                else:
                    value = line.rstrip('\n').split(': ')[1]
                    data[entry].append(float(value))
    return data


def create_plot(labels, avgs, stds, title, xlabel):
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
    plt.ylabel("Average processing time")
    plt.xlabel(xlabel)
    plt.show()


def main():
    try:
        n = sys.argv[1]
    except:
        print("Please specify number of replicas. Example: Python3 plot_throughput.py NREPLICAS TITLE XLABEL START INCREMENT")
        exit(0)
    try:
        title = sys.argv[2]
    except:
        print("Please specify plot title. Example: Python3 plot_throughput.py NREPLICAS TITLE XLABEL START INCREMENT")
        exit(0)
    try:
        xlabel = sys.argv[3]
    except:
        print("please specify plot xlabel. Example: Python3 plot_throughput.py NREPLICAS TITLE XLABEL START INCREMENT")
        exit(0)
    try:
        start = int(sys.argv[4])
    except:
        print("please specify initial value. Example: Python3 plot_throughput.py NREPLICAS TITLE XLABEL START INCREMENT")
        exit(0)
    try:
        increment = int(sys.argv[5])
    except:
        print("please specify increment. Example: Python3 plot_throughput.py NREPLICAS TITLE XLABEL START INCREMENT")
        exit(0)

    data = parse_data(n, increment, start)
    label = []
    avgs = []
    stds = []
    for key in data.keys():
        label.append(str(key))
    for d in data:
        average = np.mean(data[d])
        avgs.append(average)
        std = np.std(data[d])
        stds.append(std)
    create_plot(label, avgs, stds, title, xlabel)

if __name__ == "__main__":
    main()
