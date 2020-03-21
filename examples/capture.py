#!/usr/bin/python3
'''
Samples CH1 and Ch2 for a defined time and writes the voltage values to two files
'''
from PyHT6022.LibUsbScope import Oscilloscope
import time
# from collections import deque

############
# settings #
############
sample_time    = 60     # seconds
sample_rate    = 20e3    # slowest possible value is 20e3
channel1_gain  = 1       # 1, 2, 5, 10
channel2_gain  = 1       # 1, 2, 5, 10
############



scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.flash_firmware()
calibration = scope.get_calibration_values()

alternative    = 0       # 0 = BULK, >0 = ISO, 1=3072,2=2048,3=1024 bytes per 125 us
scope.set_interface( alternative )
#print("ISO" if scope.is_iso else "BULK", "packet size =", scope.packetsize)
scope.set_num_channels( 2 ) # 1 = CH1 only, 2 = CH1 and CH2

if sample_rate < 1e6:
    sample_id = int( 100 + sample_rate / 10e3 )
else:
    sample_id = int( sample_rate / 1e6 )
scope.set_sample_rate( sample_id )

scope.set_ch1_voltage_range( channel1_gain )
scope.set_ch2_voltage_range( channel2_gain )


def extend_callback( ch1_data, ch2_data ):
    global data1_extend
    global data2_extend
    global skip1st
    if skip1st: # skip the 1st block
        skip1st = False
        return
    ch1_scaled = scope.scale_read_data( ch1_data, channel1_gain, channel=1 )
    capture1.write(str(ch1_scaled)[1:-1].replace(', ',chr(10)))
    if len(ch1_data):
        capture1.write('\n')
    ch2_scaled = scope.scale_read_data( ch2_data, channel2_gain, channel=2 )
    capture2.write(str(ch2_scaled)[1:-1].replace(', ',chr(10)))
    if len(ch2_data):
        capture2.write('\n')


capture1 = open('capture1_{}s.out'.format( sample_time ),'wt')
capture2 = open('capture2_{}s.out'.format( sample_time ),'wt')

skip1st = True
start_time = time.time() + scope.packetsize / sample_rate # skip 1st packet
# print("Clearing FIFO and starting data transfer")
scope.start_capture()
shutdown_event = scope.read_async(extend_callback, scope.packetsize, outstanding_transfers=10, raw=True)
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

capture1.close()
capture2.close()
