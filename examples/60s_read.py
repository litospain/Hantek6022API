#!/usr/bin/python3

__author__ = 'rcope'

from PyHT6022.LibUsbScope import Oscilloscope
import matplotlib.pyplot as plt
import time
#import numpy as np
from collections import deque

sample_time = 60       # seconds
sample_rate = 102      # slowest rate is 20 kS/s, coded as below:
                       # 102,105,106,110,120,150 = 20,50,60,100,200,500 kS/s, ...
                       # ... 1,2,3,4,5,6,8,10,12,15,24,30 = 1,2,3,4,5,6,8,10,12,15,24,30 MS/s
voltage_gain = 1       # 1, 2, 5, 10
data_points = 3 * 1024 # max size for ISO xfer

scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.flash_firmware()
scope.set_interface( 0 )    # 0 = Bulk, 1 = ISO
scope.set_num_channels( 1 ) # 1 = CH1 only, 2 = CH1 and CH2
scope.set_sample_rate( sample_rate )
scope.set_ch1_voltage_range( voltage_gain )
time.sleep(1) # settle

data = deque(maxlen=1200*1024) # must hold 20 kS/s * 60 s
data_extend = data.extend


def extend_callback(ch1_data, _):
    global data_extend
    data_extend(ch1_data)

start_time = time.time()
print("Clearing FIFO and starting data transfer")
i = 0
scope.start_capture()
shutdown_event = scope.read_async(extend_callback, data_points, outstanding_transfers=10, raw=True)
print("Wait", sample_time, "seconds ..." )
while time.time() - start_time < sample_time:
    scope.poll()
scope.stop_capture()
print("Stopping new transfers.")
shutdown_event.set()
print("Snooze 1")
time.sleep(1)
print("Closing handle")
scope.close_handle()
print("Handle closed.")
print("Points in buffer:", len(data))
scaled_data = scope.scale_read_data(data, voltage_gain)
with open('60s_read.out','wt') as ouf:
    ouf.write(str(scaled_data)[1:-1].replace(', ',chr(10)))
plt.figure(0)
plt.plot(scaled_data)
plt.show()
