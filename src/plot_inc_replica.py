#!/usr/bin/env python3
from cProfile import label
import numpy as np
import matplotlib.pyplot as plt
import sys
plt.rcParams['axes.linewidth'] = 0.1


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
    xlabel = "Number of replicas"
    label = ["1", "2", "6", "16", "31", "46", "61"]
    avgs = [9.066147971, 14.53926646, 57.38884203, 90.60547394, 135.7188777, 179.0789036, 347.9772744]
    stds = [4.837350049, 6.918915243, 17.32428474, 33.57220606, 58.15579779, 58.15579779, 120.4440412]
    title = "Throughput as as function of replicas\ntimeout 0.4 secs, config (X,2,3)"
    create_plot(label, avgs, stds, title, xlabel)

if __name__ == "__main__":
    main()
