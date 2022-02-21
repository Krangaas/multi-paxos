#!/usr/bin/env python3
import numpy as np
import sys


class ConfirmConsensus:
    def __init__(self, n):
        self.n = n
        self.op = self.__get_ops__()
        self.__confirm__()

    def __get_ops__(self):
        oplist = []
        for i in range(int(self.n)):
            file = "thr_replica_"+str(i)
            tmp = []
            try:
                with open(file, mode='r') as f:
                    next(f)
                    for line in f:
                        op = line.rstrip('\n').split(':')[0]
                        tmp.append(op)
                oplist.append(tmp)
            except Exception as e:
                print(e)
                exit(0)
        return oplist

    def __confirm__(self):
        is_ok = True
        for i in range(len(self.op)):
            consensus = self.op[0] == self.op[i]
            if not consensus:
                print("Consensus not reached between replica 0 and replica", i)
                is_ok = False
        if is_ok:
            print("Ok")

def main():
    try:
        n = sys.argv[1]
    except:
        print("Please specify number of replicas")
        exit(0)
    ConfirmConsensus(n)



if __name__=='__main__':
    main()
