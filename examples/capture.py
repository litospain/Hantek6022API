#!/usr/bin/python3

__author__ = 'rcope'

from PyHT6022.LibUsbScope import Oscilloscope
import time
from collections import deque

sample_time = 6       # seconds
sample_rate = 20e3     # slowest possible value
voltage_gain = 1       # 1, 2, 5, 10
alternative = 3        # 0 = BULK, >0 = ISO, 1=3072,2=2048,3=1024 bytes per 125 us

scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.flash_firmware()

calibration = scope.get_calibration_values( 80 )

# HACK: use CH1 only, slow sampling, assume extended calibration context

offsets = { 10: calibration[0] - 128,
             5: calibration[6] - 128,
             2: calibration[8] - 128,
             1: calibration[14] - 128
         }

gains = { 10:1.01, 5:1.01, 2:1.01, 1:1.01 }


# check for extended offset correction
if calibration[48] != 0 and calibration[48] != 255:
    offsets[10] = offsets[10] +  ( calibration[48] - 128 ) / 250
if calibration[54] != 0 and calibration[54] != 255:
    offsets[5] = offsets[5] +  ( calibration[54] - 128 ) / 250
if calibration[56] != 0 and calibration[56] != 255:
    offsets[2] = offsets[2] +  ( calibration[56] - 128 ) / 250
if calibration[62] != 0 and calibration[62] != 255:
    offsets[1] = offsets[1] +  ( calibration[62] - 128 ) / 250


# check for gain correction
if calibration[32] != 0 and calibration[32] != 255:
    gains[10] = gains[10] * ( 1 + ( calibration[32] - 128 ) / 500 )
if calibration[38] != 0 and calibration[38] != 255:
    gains[5] = gains[5] * ( 1 + ( calibration[38] - 128 ) / 500 )
if calibration[40] != 0 and calibration[40] != 255:
    gains[2] = gains[2] * ( 1 + ( calibration[40] - 128 ) / 500 )
if calibration[46] != 0 and calibration[46] != 255:
    gains[1] = gains[1] * ( 1 + ( calibration[46] - 128 ) / 500 )


offset = offsets[ voltage_gain ]
gain = gains[ voltage_gain ]


scope.set_interface( alternative )    # 0 = Bulk, 1,2,... = ISO
print("ISO" if scope.is_iso else "BULK", "packet size =", scope.packetsize)
scope.set_num_channels( 1 ) # 1 = CH1 only, 2 = CH1 and CH2
if sample_rate < 1e6:
	sample_id = int( 100 + sample_rate / 10e3 )
else:
	sample_id = int( sample_rate / 1e6 )
scope.set_sample_rate( sample_id )
scope.set_ch1_voltage_range( voltage_gain )
time.sleep(1) # settle

data = deque( maxlen = int( sample_time * sample_rate / 1000 * 1024 ) ) # must hold 20 kS/s * 60 s
data_extend = data.extend
data_points = 3 * 1024 # max size for ISO xfer


def extend_callback(ch1_data, _):
    global data_extend
    data_extend(ch1_data)

start_time = time.time()
# print("Clearing FIFO and starting data transfer")
scope.start_capture()
shutdown_event = scope.read_async(extend_callback, data_points, outstanding_transfers=10, raw=True)
print("Capture", sample_time, "seconds ..." )
while time.time() - start_time < sample_time:
    scope.poll()
scope.stop_capture()
print("Stop capturing")
shutdown_event.set()
# print("Snooze 1")
time.sleep(1)
# print("Closing handle")
scope.close_handle()
# print("Handle closed.")
print("Points in buffer:", len(data))

scaled_data = scope.scale_read_data( data, voltage_gain, gain, offset )

with open('capture_{}s.out'.format( sample_time ),'wt') as capture:
    capture.write(str(scaled_data)[1:-1].replace(', ',chr(10)))
    capture.write('\n')
