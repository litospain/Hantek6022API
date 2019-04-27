#!/usr/bin/python3


from PyHT6022.LibUsbScope import Oscilloscope
import time
import sys


sample_rate_index = 1
voltage_range = 1
cal_freq = int( sys.argv[1])

# skip first samples due to unstable xfer

scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.set_sample_rate(sample_rate_index)
scope.set_ch1_voltage_range(voltage_range)
print( scope.set_calibration_frequency( cal_freq ) )
