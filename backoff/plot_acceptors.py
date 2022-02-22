#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import sys
plt.rcParams['axes.linewidth'] = 0.1

def parse_data(n):
    """ Parse data stored in n replica files """
    data = {}
    increment = 2
    for i in range(0, int(n)):
        entry = 1
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
    plt.ylabel("Throughput")
    plt.xlabel("Number of acceptors")
    plt.show()


def main():
    try:
        n = sys.argv[1]
    except:
        print("Please specify number of replicas. Example: Python3 plot_throughput.py 5")
        exit(0)
    data = parse_data(n)

    label = []
    avgs = []
    stds = []
    title = "Throughput as a function of N acceptors"


    for key in data.keys():
        label.append(key)
        print(key)
    for d in data:
        average = np.mean(data[d])
        avgs.append(average)
        std = np.std(data[d])
        stds.append(std)
    create_plot(label, avgs, stds, title)

if __name__ == "__main__":
    main()
