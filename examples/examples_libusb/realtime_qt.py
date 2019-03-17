#!/usr/bin/python3

from __future__ import print_function

__author__ = 'Robert Cope', 'Jochen Hoenicke', 'Michal Fapso'
# Based on the example_linux_recordwav.py
# - asynchronously reads data from the scope
# - processes and analyzes them in multiple worker threads
# - plots results in realtime in a Qt window

from struct import pack
import sys
import time
from collections import deque

from PyHT6022.LibUsbScope import Oscilloscope

import pylab
from threading import Thread, RLock
from queue import Queue

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np



#--------------------------------------------------
# Setup
#--------------------------------------------------
voltage_range = 1       # 1 (5V), 2 (2.6V), 5 or 10
sample_rate_index = 8         # sample rate in MHz or in 10khz
sample_rate = sample_rate_index * 1000 * 10
numchannels = 1
numseconds = 0          # number of seconds to sample (use 0 for infinity)
blocksize = 100*6*1024      # should be divisible by 6*1024
alternative = 1         # choose ISO 3072 bytes per 125 us

scope = Oscilloscope()
scope.setup()
scope.open_handle()
if (not scope.is_device_firmware_present):
	scope.flash_firmware()
else:
	scope.supports_single_channel = True;
print("Setting up scope!")

#scope.set_interface(alternative);
print("ISO" if scope.is_iso else "BULK", "packet size:", scope.packetsize)
scope.set_num_channels(numchannels)
# set voltage range
scope.set_ch1_voltage_range(voltage_range)
# set sample rate
scope.set_sample_rate(sample_rate_index)
# we divide by 100 because otherwise audacity lets us not zoom into it

data = []
data_lock = RLock()

queue = Queue()
num_worker_threads = 6


#--------------------------------------------------
# Worker threads: processing data
#--------------------------------------------------
def process_data(worker_id, queue):
	global data, voltage_range
	while True:
		i = queue.get()

		data_lock.acquire()
		try:
			print("i:",i," data len:",len(data))
			if i >= len(data): continue
			block = data[i]
		finally:
			data_lock.release()

		# Min, max is much faster with numpy array than with python list
		block['raw_np'] = np.array(block['raw'])
		block_min = block['raw_np'].min()
		block_max = block['raw_np'].max()
		[block_min, block_max] = scope.scale_read_data([block_min, block_max], voltage_range) # map raw to voltage
		block['min'] = block_min
		block['max'] = block_max
		print("process_data() worker#{} block#{} min:{} max:{}".format(worker_id, i, block_min, block_max))
		queue.task_done()
	
# Start worker threads
for i in range(num_worker_threads):
    worker = Thread(target=process_data, args=(i, queue,))
    worker.setDaemon(True)
    worker.start()


#--------------------------------------------------
# Read measurements from the scope
#--------------------------------------------------
def extend_callback(ch1_data, _):
	# Note: This function has to be kept as simple and fast as possible
	#       to prevent loss of measurements. Only copy data here. All other
	#       processing is done in worker threads afterwards.
	global data, queue
	#print("ch1_data:", ch1_data)
	#print("min:{} max:{}".format(min(ch1_data), max(ch1_data)))
	print("queue.put():",len(data))

	data_lock.acquire()
	try:
		queue.put(len(data))
		data.append({'raw':ch1_data})
	finally:
		data_lock.release()

def read_scope_data():
	start_time = time.time()
	print("Clearing FIFO and starting data transfer...")
	scope.start_capture()
	#shutdown_event = scope.read_async(extend_callback, blocksize, outstanding_transfers=10,raw=True)
	shutdown_event = scope.read_async(extend_callback, blocksize, outstanding_transfers=10)
	real_duration = 0
	while True:
		real_duration = time.time() - start_time
		print("real_duration:",real_duration)
		if numseconds > 0 and real_duration >= numseconds:
			break
		scope.poll()
	print("Stopping new transfers at {} seconds".format(real_duration))

	#scope.stop_capture()
	shutdown_event.set()
	time.sleep(1)
	scope.stop_capture()
	scope.close_handle()

	total = sum(len(block['raw']) for block in data)
	print("data_length:", total)

	queue.join()

t = Thread(target=read_scope_data)
#t.setDaemon(True)
t.start()


#--------------------------------------------------
# GUI: window & plotting
#--------------------------------------------------
win = pg.GraphicsWindow()
win.setWindowTitle('Hantek 6022BE')

# 1) Simplest approach -- update data in the array such that plot appears to scroll
#    In these examples, the array size is fixed.
p1 = win.addPlot(row=0, col=0, title='Min,max voltage')
p2 = win.addPlot(row=1, col=0, title='Min,max voltage diff')
p1.getAxis('left').setLabel('Voltage'     , units='V')
p2.getAxis('left').setLabel('Voltage diff', units='V')
data1 = np.array([])
data2 = np.array([])
curve_min = p1.plot(data1, pen=(255, 0, 0))
curve_max = p1.plot(data2, pen=(0, 255, 0))
curve_min_max_diff = p2.plot(np.array([]))

def update():
	global curve_min, curve_max, curve_min_max_diff
	MAX_BLOCKS_KEPT = 50;
	t1 = time.time()
	if len(data) > MAX_BLOCKS_KEPT:
		print("too much data:",len(data));
		data_lock.acquire()
		try:
			del(data[:(len(data) - MAX_BLOCKS_KEPT)])
			print("too much data after clearing:",len(data));
		finally:
			data_lock.release()

	t2 = time.time()
	mins = []
	maxs = []
	min_max_diff = []
	for block in data:
		if 'min' in block: mins += [block['min']]
		if 'max' in block: maxs += [block['max']]
		if 'min' in block and 'max' in block: min_max_diff += [block['max']-block['min']]
	del mins        [:1]
	del maxs        [:1]
	del min_max_diff[:1]
	t3 = time.time()
	#print("mins",mins)
	#print("maxs",maxs)
	curve_min         .setData(np.array(mins))
	curve_max         .setData(np.array(maxs))
	curve_min_max_diff.setData(np.array(min_max_diff))
	t4 = time.time()
	print("update() t2:{} t3:{} t4:{}".format(t2-t1, t3-t2, t4-t3))

timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)

QtGui.QApplication.instance().exec_()

print("Done")
