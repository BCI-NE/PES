#!/usr/bin/env python

import numpy as n
import ctypes
import sys
import os

libbsusb = None
numUSBs = None

# data chunk format
# codes (only first byte):
# 128+0..128+32+31     stimuli (+32 if target)
# 128+64+0..128+64+31  control codes:
#     128+64+0             start of run
#     128+64+31            general start of chunk
# payload (not allowed for first byte):
# 0..128               payload
TM = 0x0200  # TM (timing) bit set
DV = 0x0100  # DV (data valid) bit set
CTL = 128 # first possible stimulus
CTLe = 128 + 64 # last+1 possible stimulus (target)
TRG = 32 # target flag
SOR = 128 + 64 # start of run
EOR = 128 + 64 + 1 # end of run
UNK = 128 + 64 + 31 # unknown / unspecified chunk of data


def donothing(*args, **kwargs):
    pass


all_send = donothing
all_close = donothing


def all_dosend(X, code=128+64+31):
    global libbsusb
    # cast the data to a string
    blk = data2string(X)
    # add code as start of message
    if not code is None:
        blk = chr(code) + blk
    for which_usb in range(numUSBs):
        libbsusb.bsusb_multiple_sendctl(which_usb, 0x40,0,2,0)
        libbsusb.bsusb_multiple_senda(which_usb, blk, len(blk))


def all_init(path=None):
    global libbsusb
    global all_send, all_close
    all_send = all_dosend
    all_close = all_close_usb
    snowplough = n.zeros((256,), dtype=n.uint8)
    if not libbsusb:
        multiple_find(path)
    for which_usb in range(numUSBs):
        libbsusb.bsusb_multiple_init(which_usb)
        libbsusb.bsusb_multiple_senda(which_usb,snowplough.tostring(), len(snowplough))

def all_close_usb():
    for which_usb in range(numUSBs):
        libbsusb.bsusb_multiple_close(which_usb)

multiple_send = donothing
multiple_close = donothing

def data2string(X):
    # cast the data to a string
    tX = type(X)
    if tX == str:
        blk = X
    elif tX == int:
        blk = n.uint8(X).tostring()
    elif tX == n.ndarray:
        if X.dtype == n.uint8:
            blk = X.tostring()
    else:
        raise TypeError
    return blk

def multiple_dosend(which_usb, X, code=128+64+31):
    global libbsusb
    # force a reset of the tx buffer of the UM245R. This makes TXE active for about 100ns
    # and sets the 7496 shift register, then the BioSemi clock CK extracts the bits at every clock:
    # - if the TXE spike happens in the low phase CK, just one sample is marked,
    # - if it happens in the high phase of CK, two samples are marked;
    # this allows a time resolution 2 times finer than 1/(sampl freq)
    libbsusb.bsusb_multiple_sendctl(which_usb, 0x40,0,2,0)
    # cast the data to a string
    blk = data2string(X)
    # add code as start of message
    if not code is None:
        blk = chr(code) + blk
    # send the data
    libbsusb.bsusb_multiple_senda(which_usb, blk, len(blk))

def load(path=None):
    global libbsusb
    if path is None:
        path = os.path.dirname(__file__)
        if len(path) == 0:
            path = "."
    path += "/"
    if sys.platform.startswith('linux'):
        libbsusb = ctypes.CDLL(path + "libbsusb.so")
    elif sys.platform.startswith('win'):
        libbsusb = ctypes.CDLL(path + "libbsusb.dll")
    elif sys.platform.startswith('darwin'):
        libbsusb = ctypes.CDLL(path + "Idontknow")

def multiple_find(path=None):
    global libbsusb, numUSBs
    if not libbsusb:
        load(path)
    numUSBs = libbsusb.bsusb_multiple_find()
    return numUSBs

def multiple_init(which_usb,path=None):
    global libbsusb
    if not libbsusb:
        multiple_find(path=None)
    libbsusb.bsusb_multiple_init(which_usb)
    global multiple_send, multiple_close
    multiple_send = multiple_dosend
    multiple_close = libbsusb.bsusb_multiple_close
    snowplough = n.zeros((256,), dtype=n.uint8)
    libbsusb.bsusb_multiple_senda(which_usb,snowplough.tostring(), len(snowplough))


# OLD VERSION OF CODE KEPT FOR BACKWARD COMPATIBILITY

send = donothing
close = donothing

def dosend(X, code=128+64+31):
    global libbsusb
    # force a reset of the tx buffer of the UM245R. This makes TXE active for about 100ns
    # and sets the 7496 shift register, then the BioSemi clock CK extracts the bits at every clock:
    # - if the TXE spike happens in the low phase CK, just one sample is marked,
    # - if it happens in the high phase of CK, two samples are marked;
    # this allows a time resolution 2 times finer than 1/(sampl freq)
    libbsusb.bsusb_sendctl(0x40,0,2,0)
    # cast the data to a string
    blk = data2string(X)
    # add code as start of message
    if not code is None:
        blk = chr(code) + blk
    # send the data
    libbsusb.bsusb_senda(blk, len(blk))


def init(path=None, loadonly=False):
    global libbsusb
    if not libbsusb:
        load(path)
    if not loadonly:
        libbsusb.bsusb_init()
        global send, close
        send = dosend
        close = libbsusb.bsusb_close
        snowplough = n.zeros((256,), dtype=n.uint8)
        libbsusb.bsusb_senda(snowplough.tostring(), len(snowplough))

if __name__ == "__main__":
#    init(path=sys.path[0] or os.curdir, loadonly=True)
    import time
    multiple_find(path=sys.path[0] or os.curdir)
    # print 'number of USBs', numUSBs
    # if numUSBs > 1:
    #     multiple_init(0)
    #     multiple_init(1)
    #     for i in range(10):
    #         multiple_send(0,'HELLO!!!!')
    #         multiple_send(1,'CHEERS!!!!'*20)
    #         time.sleep(1)
    #     multiple_close(0)
    #     multiple_close(1)
    all_init()
    print 'number of USBs', numUSBs
    for i in range(10):
        all_send('HELLO!!!!')
        time.sleep(1)
    all_close()
