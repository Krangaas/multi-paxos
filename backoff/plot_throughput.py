#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import csv
import sys
import random
plt.rcParams['axes.linewidth'] = 0.1

def parse_data(n):
    """ Parse data stored in replica files """
    data = []
    for i in range(int(n)):
        with open("thr_replica_"+str(i), mode='r') as f:
            next(f) # skip header
            for line in f:
                value = line.rstrip('\n').split(': ')[1]
                data.append(float(value))
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
    plt.xlabel("Number of clients")
    plt.show()


def main():
    try:
        n = sys.argv[1]
    except:
        print("Please specify number of replicas")
        exit(0)
    data = parse_data(n)
    label = []
    avgs = []
    stds = []

    label = n
    title = "Throughtput as a function of N clients"
    avgs = np.mean(data)
    stds = np.std(data)
    create_plot(label, avgs, stds, title)


if __name__ == "__main__":
    main()
