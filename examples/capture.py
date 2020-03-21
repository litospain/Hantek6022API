#!/usr/bin/python3
'''
Samples CH1 and Ch2 for a defined time and writes the time stamp and the voltage values to a file
'''
from PyHT6022.LibUsbScope import Oscilloscope
import time
# from collections import deque

############
# settings #
############
sample_time    = 60      # seconds
sample_rate    = 20e3    # slowest possible value is 20e3 (20k, 50k, 100k, ... , 10M
channel1_gain  = 1       # 1, 2, 5, 10
channel2_gain  = 1       # 1, 2, 5, 10
############



scope = Oscilloscope()
scope.setup()
scope.open_handle()

# upload firmware into device's RAM
if (not scope.is_device_firmware_present):
    scope.flash_firmware()

# read calibration values from EEPROM
calibration = scope.get_calibration_values()

# set interface: 0 = BULK, >0 = ISO, 1=3072,2=2048,3=1024 bytes per 125 us
scope.set_interface( 0 )
#print("ISO" if scope.is_iso else "BULK", "packet size =", scope.packetsize)

# set number of channels: 1 = CH1 only, 2 = CH1 and CH2
scope.set_num_channels( 2 )

# calculate and set the sample rate ID from real sample rate value
if sample_rate < 1e6:
    sample_id = int( 100 + sample_rate / 10e3 )
else:
    sample_id = int( sample_rate / 1e6 )
scope.set_sample_rate( sample_id )

# set the gain for CH1 and CH2
scope.set_ch1_voltage_range( channel1_gain )
scope.set_ch2_voltage_range( channel2_gain )


# this callback is called every time when data packets arrive
# scale the data packets and write them into the file
def packet_callback( ch1_data, ch2_data ):
    global skip1st, timestep, tick
    if skip1st: # skip the 1st block
        skip1st = False
        return
    ch1_scaled = scope.scale_read_data( ch1_data, channel1_gain, channel=1 )
    ch2_scaled = scope.scale_read_data( ch2_data, channel2_gain, channel=2 )
    for ch1_value, ch2_value in zip( ch1_scaled, ch2_scaled ): # merge CH1 & CH2
        capture.write( "{:<10.4g} {:< 10.4g} {:< 10.4g}\n".format( timestep, ch1_value, ch2_value ) )
        timestep = timestep + tick


# create file for time stamp and sample values of both channels
capture = open('capture_{}s.out'.format( sample_time ),'wt')

skip1st = True # marker for skip of 1st (unstable) packet
tick = 1 / sample_rate
timestep = 0
start_time = time.time() + scope.packetsize / sample_rate # add time for 1st skipped packet
scope.start_capture()
shutdown_event = scope.read_async( packet_callback, scope.packetsize, outstanding_transfers=10, raw=True)
print("Capture", sample_time, "seconds ..." )

# sample until time is over
while time.time() - start_time < sample_time:
    scope.poll()
scope.stop_capture()
shutdown_event.set()

# fetch remaining packets before closing the scope
time.sleep(1)
scope.close_handle()

capture.close()
