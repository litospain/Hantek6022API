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

import traceback


#--------------------------------------------------
# Setup
#--------------------------------------------------
voltage_range     = 1 # 1 (5V), 2 (2.6V), 5 or 10
sample_rate_index = 8 # sample rate in MHz or in 10khz
sample_rate       = sample_rate_index * 1000 * 1000
numchannels       = 1 # number of channels to process (use 1 or 2)
numseconds        = 0 # number of seconds to sample (use 0 for infinity)
blocksize         = 100*6*1024 # should be divisible by 6*1024
block_splits_count = 10 # to make finer grained statistics
max_blocks_kept   = 30 # number of blocks to keep in memory and in plots
alternative       = 1 # choose ISO 3072 bytes per 125 us

scope = Oscilloscope()
scope.setup()
scope.open_handle()
if (not scope.is_device_firmware_present):
	scope.flash_firmware()
else:
	scope.supports_single_channel = True;
print("Setting up scope!")

#scope.set_interface(alternative)
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

paused = False


#--------------------------------------------------
# Worker threads: processing data
#--------------------------------------------------
def samples_to_seconds(samplesCount):
	global sample_rate, numchannels
	sample_rate_per_channel = sample_rate / numchannels
	print('samples_to_seconds()',samplesCount / sample_rate_per_channel)
	return samplesCount / sample_rate_per_channel

def reshape_fit(a, newColCount):
	to_add = len(a) % newColCount
	if to_add > 0: to_add = newColCount - to_add
	print('reshape_fit() a1:',a.shape, 'newColCount:',newColCount, 'to_add',to_add)
	a = np.append(a, np.ones(to_add, dtype=a.dtype) * a[len(a)-1])
	print('reshape_fit() a2:',a.shape)
	return a.reshape(-1, newColCount)
	#.min(axis=1)

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

		t1 = time.time()
		# Min, max is much faster with numpy array than with python list
		for ch in range(0, numchannels):
			print('block length:{}'.format(len(block)))
			block_ch = block[ch]
			print('block_ch length:{}'.format(len(block_ch)))
			print('block_ch[raw] length:{}'.format(len(block_ch['raw'])))
			if (len(block_ch['raw']) == 0):
				continue
			block_ch['raw_np'] = np.array(block_ch['raw'])
			block_min = block_ch['raw_np'].min()
			block_max = block_ch['raw_np'].max()
			[block_min_voltage, block_max_voltage] = scope.scale_read_data([block_min, block_max], voltage_range) # map raw to voltage
			block_ch['min'] = block_min_voltage
			block_ch['max'] = block_max_voltage
			# Linear conversion from raw measurements to voltage:
			conv_mul    = (block_max_voltage - block_min_voltage) / (block_max - block_min)
			conv_offset = block_min_voltage - block_min * conv_mul
			# Multiple min,max per block
			raw_np_splits  = reshape_fit(block_ch['raw_np'], block_splits_count)
			block_ch['min_splits'    ] = conv_offset + raw_np_splits.min(axis=0) * conv_mul
			block_ch['max_splits'    ] = conv_offset + raw_np_splits.max(axis=0) * conv_mul
			block_ch['raw_np_voltage'] = conv_offset + block_ch['raw_np']        * conv_mul
			#block_ch['min_splits'] = np.array(scope.scale_read_data(raw_np_splits.min(axis=0).tolist(), voltage_range)) # map raw to voltage
			#block_ch['max_splits'] = np.array(scope.scale_read_data(raw_np_splits.max(axis=0).tolist(), voltage_range)) # map raw to voltage
			print('process_data() min_splits:',block_ch['min_splits'].shape)

			#block_ch['raw_np_voltage'] = np.array(block_ch['raw'])
			print("process_data() worker#{} block#{} ch:{} min:{} max:{}".format(worker_id, i, ch, block_min, block_max))
		t2 = time.time()
		print('process_data() tTotal:{}'.format(t2-t1))
		queue.task_done()
	
# Start worker threads
for i in range(num_worker_threads):
    worker = Thread(target=process_data, args=(i, queue,))
    worker.setDaemon(True)
    worker.start()


#--------------------------------------------------
# Read measurements from the scope
#--------------------------------------------------
def extend_callback(ch0_data, ch1_data):
	# Note: This function has to be kept as simple and fast as possible
	#       to prevent loss of measurements. Only copy data here. All other
	#       processing is done in worker threads afterwards.
	global data, queue, paused
	if paused: return

	#print("ch0_data:", ch0_data)
	#print("min:{} max:{}".format(min(ch0_data), max(ch0_data)))
	print("queue.put(): len(data):",len(data)," len(ch0_data):",len(ch0_data)," len(ch1_data):",len(ch1_data))

	data_lock.acquire()
	try:
		queue.put(len(data))
		data.append([{'raw':ch0_data},{'raw': ch1_data}])
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
		if paused:
			time.sleep(1)
		else:
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

	total = sum(len(block[0]['raw']) for block in data)
	print("data_length:", total)

	queue.join()

t = Thread(target=read_scope_data)
#t.setDaemon(True)
t.start()


#--------------------------------------------------
# GUI: window & plotting
#--------------------------------------------------
class Gui:
	def __init__(self):
		global numchannels, blocksize
		self.timer = pg.QtCore.QTimer()
		self.win = pg.GraphicsWindow()
		self.win.setWindowTitle('Hantek 6022BE')

		# 1) Simplest approach -- update data in the array such that plot appears to scroll
		#    In these examples, the array size is fixed.
		self.p_minmax           = []
		self.p_diff             = []
		self.p_detail           = []
		self.lr                 = []
		self.curve_min          = []
		self.curve_max          = []
		self.curve_min_max_diff = []
		self.curve_detail       = []

		# button 'pause'
		self.button_pause = QtGui.QPushButton()
		self.proxy_pause = QtGui.QGraphicsProxyWidget()
		self.button_pause = QtGui.QPushButton('pause')
		self.proxy_pause.setWidget(self.button_pause)
		self.button_pause.clicked.connect(lambda state: self.button_pause_clicked())

		self.p_buttons = self.win.addLayout(row=0, col=0, colspan=2)
		self.p_buttons.addItem(self.proxy_pause,row=0,col=0)

		# plots
		for ch in range(0, numchannels):
			self.p_minmax          .append(self.win.addPlot(row=1, col=ch, title='Ch{} min,max voltage'     .format(ch)))
			self.p_diff            .append(self.win.addPlot(row=2, col=ch, title='Ch{} min,max voltage diff'.format(ch)))
			self.p_detail          .append(self.win.addPlot(row=3, col=ch, title='CH{} detail'              .format(ch)))
			self.lr                .append(pg.LinearRegionItem([1,2]))
			self.lr      [ch].setZValue(-10)
			self.lr      [ch].sigRegionChanged.connect(lambda: self.lr_OnRegionChanged(ch))
			self.p_detail[ch].sigXRangeChanged.connect(lambda: self.p_detail_OnXRangeChanged(ch))
			self.p_minmax[ch].sigXRangeChanged.connect(lambda: self.p_minmax_OnXRangeChanged(ch))
			self.p_diff  [ch].sigXRangeChanged.connect(lambda: self.p_diff_OnXRangeChanged(ch))
			self.p_detail_OnXRangeChanged(ch)

			#p_minmax[ch].addItem(lr[ch])
			self.p_minmax[ch].getAxis('left').setLabel('Voltage'     , units='V')
			self.p_diff  [ch].getAxis('left').setLabel('Voltage diff', units='V')
			self.p_detail[ch].getAxis('left').setLabel('Voltage'     , units='V')
			self.p_minmax[ch].getAxis('bottom').setLabel('Time', units='s')
			self.p_diff  [ch].getAxis('bottom').setLabel('Time', units='s')
			self.p_detail[ch].getAxis('bottom').setLabel('Time', units='s')
			self.p_minmax[ch].setMouseEnabled(x=True, y=False)
			self.p_diff  [ch].setMouseEnabled(x=True, y=False)
			self.p_detail[ch].setMouseEnabled(x=True, y=False)
			self.p_detail[ch].disableAutoRange('x')
			print('p_detail setXRange(0, ',samples_to_seconds(blocksize / numchannels), blocksize, numchannels)
			self.p_detail[ch].setXRange(0, samples_to_seconds(blocksize / numchannels), padding=0)
			self.curve_min         .append(self.p_minmax[ch].plot(np.array([]), pen=(255, 0, 0)))
			self.curve_max         .append(self.p_minmax[ch].plot(np.array([]), pen=(0, 255, 0)))
			self.curve_min_max_diff.append(self.p_diff  [ch].plot(np.array([])))
			self.curve_detail      .append(self.p_detail[ch].plot(np.array([])))

		self.timer.timeout.connect(lambda: self.update())
		self.timer.start(50)

	def button_pause_clicked(self):
		global paused, numchannels
		paused = not paused
		if not paused: self.timer.start()
		for ch in range(0, numchannels):
			if paused:
				#r = [(len(data)-2) * block_splits_count, (len(data)-1) * block_splits_count]
				#print('lr setRegion:', r)
				#self.lr[ch].setRegion(r)
				self.p_minmax[ch].addItem(self.lr[ch])
				r = [samples_to_seconds((len(data)-2) * blocksize / numchannels),
					 samples_to_seconds((len(data)-1) * blocksize / numchannels)]
				#self.p_detail[ch].setXRange(*r, padding=0)
				#self.p_diff  [ch].addItem(self.lr[ch])
			else:
				self.p_minmax[ch].removeItem(self.lr[ch])
				#self.p_diff  [ch].removeItem(self.lr[ch])
				print('p_detail setXRange(0, ',samples_to_seconds(blocksize / numchannels), blocksize, numchannels)
				self.p_detail[ch].setXRange(0, samples_to_seconds(blocksize / numchannels), padding=0)
		self.update()
		#QtGui.QMessageBox.information(None, 'Title', 'paused:{}'.format(paused))


	def lr_OnRegionChanged(self, ch):
		global paused, blocksize, numchannels
		#return
		if not paused: return
		#r = [0, 100]
		r = self.lr[ch].getRegion()
		print('lr_OnRegionChanged() r:',self.lr[ch].getRegion(),' -> ',r)
		self.p_detail[ch].setXRange(*r, padding=0)

	def p_detail_OnXRangeChanged(self, ch):
		global paused, blocksize, numchannels
		#return
		if not paused: return
		#r = [0, 10]
		r = self.p_detail[ch].getViewBox().viewRange()[0]
		print('p_detail_OnXRangeChanged() range:',self.p_detail[ch].getViewBox().viewRange(),' range[0]:',self.p_detail[ch].getViewBox().viewRange()[0],' -> ',r)
		self.lr[ch].setRegion(r)

	def p_minmax_OnXRangeChanged(self, ch):
		r = self.p_minmax[ch].getViewBox().viewRange()[0]
		self.p_diff[ch].setXRange(*r, padding=0)

	def p_diff_OnXRangeChanged(self, ch):
		r = self.p_diff[ch].getViewBox().viewRange()[0]
		self.p_minmax[ch].setXRange(*r, padding=0)

	def set_curve_data_full(self, curve, a):
		curve.setData(y=a, x=np.linspace(0, samples_to_seconds(len(a)-1), len(a)))

	def set_curve_data_splits(self, curve, a):
		global blocksize, block_splits_count
		curve.setData(y=a, x=np.linspace(0, samples_to_seconds((len(a)-1) * blocksize / block_splits_count), len(a)))

	def update(self):
		global paused, data, data_lock, max_blocks_kept
		if paused: self.timer.stop()
		t1 = time.time()
		if len(data) > max_blocks_kept:
			print("too much data:",len(data));
			data_lock.acquire()
			try:
				del(data[:(len(data) - max_blocks_kept)])
				print("too much data after clearing:",len(data));
			finally:
				data_lock.release()

		t2 = time.time()
		mins         = []
		maxs         = []
		min_max_diff = []
		raw_np       = []
		last_block   = None
		for ch in range(0, numchannels):
			mins        .append(np.array([]))
			maxs        .append(np.array([]))
			min_max_diff.append(np.array([]))
			raw_np      .append(np.array([]))
		print('data size:',len(data))
		for block in data:
			for ch in range(0, numchannels):
				min_idx = 'min_splits'
				max_idx = 'max_splits'
				if min_idx in block[ch]: print('update()',min_idx,block[ch][min_idx].shape)
				if min_idx in block[ch]: print('update() mins:',mins[ch].shape)
				if min_idx in block[ch]: mins[ch] = np.append(mins[ch], block[ch][min_idx])
				if max_idx in block[ch]: maxs[ch] = np.append(maxs[ch], block[ch][max_idx])
				if min_idx in block[ch] and max_idx in block[ch]: min_max_diff[ch] = np.append(min_max_diff[ch], block[ch][max_idx]-block[ch][min_idx])
				if 'raw_np' in block[ch] and paused: raw_np[ch] = np.append(raw_np[ch], block[ch]['raw_np_voltage'])

				#raw_np[ch] = np.concatenate(raw_np[ch], block[ch]['raw_np'])
				#raw_np[ch].append(block[ch]['raw_np'])
			last_block = block
		#print("update() ch0:{}..{} ch1:{}..{}".format(mins[0][0], maxs[0][0], mins[1][0], maxs[1][0]))
		t3 = time.time()
		#print("mins",mins)
		#print("maxs",maxs)
		for ch in range(0, numchannels):
			self.set_curve_data_splits(self.curve_min         [ch], mins        [ch])
			self.set_curve_data_splits(self.curve_max         [ch], maxs        [ch])
			self.set_curve_data_splits(self.curve_min_max_diff[ch], min_max_diff[ch])
			if paused:
				self.set_curve_data_full(self.curve_detail[ch], raw_np[ch])
				#r = [(len(data)-2) * block_splits_count, (len(data)-1) * block_splits_count]
				r = [samples_to_seconds((len(data)-2) * blocksize / numchannels),
					 samples_to_seconds((len(data)-1) * blocksize / numchannels)]
				print('p_detail setXRange:', r, len(data), blocksize, numchannels)
				#self.lr[ch].setRegion(r)
				self.p_detail[ch].setXRange(*r, padding=0)
				#self.lr_OnRegionChanged(ch)
			else:
				if 'raw_np_voltage' in last_block[ch]: self.set_curve_data_full(self.curve_detail[ch], last_block[ch]['raw_np_voltage'])

			r = [0, samples_to_seconds((len(data)-1) * blocksize / numchannels)]
			print('p_minmax.setXRange()',r)
			self.p_minmax[ch].setXRange(*r, padding=0)
		t4 = time.time()
		print("update() tTotal:{} t2:{} t3:{} t4:{}".format(t4-t1, t2-t1, t3-t2, t4-t3))

gui = Gui()
QtGui.QApplication.instance().exec_()

print("Done")
