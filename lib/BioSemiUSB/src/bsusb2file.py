#!/usr/bin/env python

import numpy as n
import ctypes
import sys
import os
import time
import datetime as dt

libbsusb = None
numUSBs = None
fileHandler = None
start = None

# data chunk format
# codes (only first byte):
# 128+0..128+32+31	 stimuli (+32 if target)
# 128+64+0..128+64+31  control codes:
#	 128+64+0			 start of run
#	 128+64+31			general start of chunk
# payload (not allowed for first byte):
# 0..128			   payload
TM = 0x0200  # TM (timing) bit set
DV = 0x0100  # DV (data valid) bit set
CTL = 128 # first possible stimulus
CTLe = 128 + 64 # last+1 possible stimulus (target)
TRG = 32 # target flag
SOR = 128 + 64 # start of run
EOR = 128 + 64 + 1 # end of run
UNK = 128 + 64 + 31 # unknown / unspecified chunk of data

# USB FILE FORMAT
# - CTL messages are composed by the marker [CTL] and the parameters space separated (written as a string), ending with marker [/CTL]
# - before the data message, command decimal code is printed
# - after data message, a line break is appended to the file
#
# The program write on only 1 USB, but if you change the value on line 129, it should be working


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
		FileHandler.write('[CTL] 0x40 0 2 0 [/CTL]') # write CTL message with parameters
		pickle.dump(blk,fileHandler) # write the blk array
	fileHandler.write('\n'); #print separator = line break


def all_init(path=None, fileName="usbdata.dat"):
	global libbsusb
	global all_send, all_close
	global fileHandler
	global start
	start = dt.datetime.now()
	all_send = dosend
	all_close = all_close_usb
	fileHandler = open(fileName,'w')
	#snowplough = n.zeros((256,), dtype=n.uint8)
	#if not libbsusb:
		#multiple_find(path)
	#for which_usb in range(numUSBs):
		#pickle.dump(snowplough, fileHandler) # write the snowplough array
	#fileHandler.write('\n##### INIT END #####\n'); #print separator = line break

def all_close_usb():
	fileHandler.close() # simply close the file
	print("CLOSING FILE...")

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
	fileHandler.write('[CTL] 0x40 0 2 0 [/CTL]\n') # write CTL message with parameters and line break
	# cast the data to a string
	blk = data2string(X)
	# add code as start of message
	if not code is None:
		blk = str(code) + " " + blk
	# send the data
	fileHandler.write(blk) # write the blk array
	fileHandler.write('\n'); #print separator = line break

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
	global numUSBs
	# for testing purposes, send to 1 USB only
	numUSBs = 1
	return numUSBs

def multiple_init(which_usb,path=None):
	multiple_find(path=None)
	global multiple_send, multiple_close
	multiple_send = multiple_dosend
	multiple_close = all_close_usb
	snowplough = n.zeros((256,), dtype=n.uint8)
	pickle.dump(snowplough,fileHandler) # write the snowplough array
	fileHandler.write('\n'); #print separator = line break


# OLD VERSION OF CODE KEPT FOR BACKWARD COMPATIBILITY

send = donothing
close = donothing

def dosend(X, code=128+64+31):
	global start
	# force a reset of the tx buffer of the UM245R. This makes TXE active for about 100ns
	# and sets the 7496 shift register, then the BioSemi clock CK extracts the bits at every clock:
	# - if the TXE spike happens in the low phase CK, just one sample is marked,
	# - if it happens in the high phase of CK, two samples are marked;
	# this allows a time resolution 2 times finer than 1/(sampl freq)
	fileHandler.write('[CTL] 0x40 0 2 0 [/CTL]\n') # write CTL message with parameters and line break
	# cast the data to a string
	blk = data2string(X)
	# add code as start of message
	if not code is None:
		blk = str(code) + " " + blk
	# send the data
	t = dt.datetime.now()-start
	fileHandler.write(str(t.seconds)+"."+str(t.microseconds).zfill(6)+" "+blk) # write the blk array
	fileHandler.write('\n'); #print separator = line break


def init(path=None, loadonly=False, fileName="usbdata.dat"):
	global start
	start = dt.datetime.now()
	if not loadonly:
		global fileHandler
		fileHandler = open(fileName,'w')
		global send, close
		send = dosend
		close = all_close_usb
		#snowplough = n.zeros((256,), dtype=n.uint8)
		#pickle.dump(snowplough,fileHandler) # write the snowplough array
		#fileHandler.write('\n##### INIT END #####\n'); #print separator = line break

if __name__ == "__main__":
	import time
	multiple_find(path=sys.path[0] or os.curdir)
	all_init()
	print( 'number of USBs', numUSBs )
	for i in range(10):
		all_send('HELLO!!!!')
		time.sleep(1)
	all_close()
