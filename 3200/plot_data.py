#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import csv
import sys
import random
plt.rcParams['axes.linewidth'] = 0.1

def parse_data(file):
    """ Parse data stored in 'data.csv' """
    with open(file, mode='r') as f:
        data = []
        csv_reader = csv.reader(f, delimiter=",")
        label = (next(csv_reader))
        for row in csv_reader:
            set = []
            nodes = row[0]
            values = row[1].strip('][').split(', ')
            values = list(map(float, values))
            set.append(nodes)
            set.append(values)
            data.append(set)
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
    plt.xlabel("Number of nodes")
    plt.show()


def main():
    try:
        file = sys.argv[1]
    except:
        print("Please specify file to read from")
        exit(0)
    data = parse_data(file)

    label = []
    avgs = []
    stds = []
    if file == "simple.csv":
        title = "Plot of average throughput, requesting from same node"
    elif file == "different.csv":
        title = "Plot of average throughput, requesting from different nodes"
    else:
        title = "Plot of average throughput, requesting non-existing key"
    for set in data:
        label.append(set[0])
        avgs.append(np.mean(set[1]))
        stds.append(np.std(set[1]))
    create_plot(label, avgs, stds, title)


if __name__ == "__main__":
    main()
