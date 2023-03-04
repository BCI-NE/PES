#!/usr/bin/python

class net(object):
    
    def __init__(self, net, oper):
        self.oper = oper
        self.oper_inputs = oper.func_code.co_argcount
        self.net = net
        self.net_c = len(net)
        if self.net_c % self.oper_inputs:
            raise ValueError
        self.parts = self.net_c // self.oper_inputs
    
    def step(self, inp):
        while 1:
            out = inp[:]
            for i in range(self.parts):
                args = [inp[self.net[i * self.oper_inputs + j]] for j in range(self.oper_inputs)] 
                out[i] = self.oper(*args)
            return out


def op_nand(a, b):
    return not (a and b)

def op_nor(a, b):
    return not (a or b)

def op_xor(a, b):
    return a != b

H = True
L = False
X = None

# to generate RD
des_inp = [[H,L],[H,L],[H,H],[H,H],[H,L],[H,L],[H,H],[H,H],[L,H],[L,L],[L,L],[L,L],[L,H],[L,H],[L,H],[L,L],[L,L],[L,L],[L,H],[L,H],[L,H],[L,L],[H,L],[H,L],[H,H],[H,H],[H,H],[H,L],[H,L],[H,L]]
des_out =   [X,    X,    X,    X,    H,    H,    H,    H,    H,    H,    H,    H,    L,    L,    L,    H,    H,    H,    L,    L,    L,    H,    H,    H,    H,    H,    H,    H,    H,    H]
# for the exact timing issue (not working with NANDs or NORs)
#des_inp = [[L,L],[L,L],[L,L],[L,H],[H,H],[L,H],[L,L],[L,L],[L,L],[L,H],[L,H],[L,H],[L,L],[L,L],[L,L],[L,H],[L,H],[L,H],[L,L],[L,L],[H,L],[L,H],[L,H],[L,H]]
#des_out =   [X,    X,    X,    L,    X,    X,    X,    X,    X,    H,    H,    H,    X,    X,    X,    L,    L,    L,    X,    X,    X,    H,    H,    H]

def test(net_n, status_n, oper):
    global des_inp, des_out
    a = net(net_n, oper)
    inp = [bool(status_n & 1<<i) for i in range(a.parts)]
    for i in range(len(des_out)):
        inp[a.parts:] = des_inp[i]
        for j in range(a.parts + 1):
            out = a.step(inp)
            if j and inp == out: # it speeds up a factor 2
                break
            inp = out
        if j == a.parts:
            return False # it is oscillating
        if (not des_out[i] is None) and (out[0] != des_out[i]):
            return False
    return True

import time
import sys

if __name__ == '__main__':
    oper = op_nand
    t = time.time()
#    print "Test"
#    print test((4, 4, 5, 6, 1, 3, 2, 5, 2, 1), 4, op_nor)
#    print time.time() - t
    args = sys.argv
    if len(args) == 3:
        (worker, workers) = (int(args[1]), int(args[2]))
    else:
        (worker, workers) = (0, 1)
    i = 0
    for n0 in range(6):
        for n1 in range(n0, 6):
            for n2 in range(6):
                for n3 in range(n2, 6):
                    sys.stderr.write("\b" * 40 + "(%d,%d,%d,%d, ...) %d" % (n0, n1, n2, n3, i))
                    for n4 in range(6):
                        for n5 in range(n4, 6):
                            for n6 in range(6):
                                for n7 in range(n6, 6):
                                    for s in range(16)[worker::workers]:
                                        n = (n0, n1, n2, n3, n4, n5, n6, n7)
                                        if test(n, s, oper):
                                            print "Working: %s %02d" % (str(n), s)
                                        i += 1
    sys.stderr.write("\nWorker %d done.\n" % worker)


