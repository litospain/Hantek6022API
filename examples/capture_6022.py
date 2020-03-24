#!/usr/bin/python3
'''
Samples CH1 and Ch2 for a defined time and writes the time stamp and the voltage values to a file

usage: capture.py [-h] [-c CHANNELS] [-s SAMPLERATE] [-x CH1GAIN] [-y CH2GAIN] [-t TIME]

optional arguments:
  -h, --help            show this help message and exit
  -c CHANNELS, --channels CHANNELS
                        how many channels to capture, default: 2
  -s SAMPLERATE, --samplerate SAMPLERATE
                        sample rate (20e3, 50e3, 64e3, 100e3, default: 20e3)
  -x CH1GAIN --ch1gain CH1GAIN
                        gain of channel 1 (1, 2, 5, 10, default: 1)
  -y CH2GAIN --ch2gain CH2GAIN
                        gain of channel 2 (1, 2, 5, 10, default: 1)
  -t TIME, --time TIME  capture time (default: 60 s)
'''

from PyHT6022.LibUsbScope import Oscilloscope
import math
import time
import argparse
import sys

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
#ap.add_argument( "-c", "--channels", type = int, default = 2,
#    help="how many channels to capture, default: 2" )
ap.add_argument( "-d", "--downsample", action = "store_true",
    help="downsample 256x" )
ap.add_argument( "-r", "--rate", type = float, default = 20,
    help="sample rate in kS/s (20, 50, 64, 100, default: 20)" )
ap.add_argument( "-t", "--time", type = float, default = 60,
    help="capture time in seconds (default: 60)" )
ap.add_argument( "-x", "--ch1", type = int, default = 1,
    help="gain of channel 1 (1, 2, 5, 10, default: 1)" )
ap.add_argument( "-y", "--ch2", type = int, default = 1,
    help="gain of channel 2 (1, 2, 5, 10, default: 1)" )

args = vars(ap.parse_args())

############
# settings #
############
#
channels    = 2
downsample  = args["downsample"]
sample_rate = int(args["rate"])
sample_time = args["time"]
ch1gain     = args["ch1"]
ch2gain     = args["ch2"]

valid_sample_rates = ( 20, 50, 64, 100 )
valid_gains = ( 1, 2, 5, 10 )

argerror = False
if sample_rate not in valid_sample_rates:
    print( "error, samplerate must be one of:", valid_sample_rates )
    argerror = True
else:
    sample_rate = sample_rate * 1000 # kS/s -> S/s
if ch1gain not in valid_gains:
    print( "error, ch1gain must be one of:", valid_gains )
    argerror = True
if ch2gain not in valid_gains:
    print( "error, ch2gain must be one of:", valid_gains )
    argerror = True
if argerror:
    sys.exit()
#
############


scope = Oscilloscope()
scope.setup()
scope.open_handle()

# upload correct firmware into device's RAM
if (not scope.is_device_firmware_present):
    scope.flash_firmware()

# read calibration values from EEPROM
calibration = scope.get_calibration_values()

# set interface: 0 = BULK, >0 = ISO, 1=3072,2=2048,3=1024 bytes per 125 us
scope.set_interface( 0 ) # use BULK unless you have specific need for ISO xfer
#print("ISO" if scope.is_iso else "BULK", "packet size =", scope.packetsize)

scope.set_num_channels( channels )

# calculate and set the sample rate ID from real sample rate value
if sample_rate < 1e6:
    sample_id = int( 100 + sample_rate / 10e3 )
else:
    sample_id = int( sample_rate / 1e6 )
scope.set_sample_rate( sample_id )

# set the gain for CH1 and CH2
scope.set_ch1_voltage_range( ch1gain )
scope.set_ch2_voltage_range( ch2gain )


# this callback is called every time when data packets arrive
# scale the data packets and write them into the file
def packet_callback( ch1_data, ch2_data ):
    global skip1st, start_time, timestep, tick
    global totalsize, dc1, dc2, rms1, rms2
    size = len( ch1_data )
    if( size == 0 ):
        return
    if skip1st: # skip the 1st block
        skip1st = False
        return
    totalsize = totalsize + size
    ch1_scaled = scope.scale_read_data( ch1_data, ch1gain, channel=1 )
    ch2_scaled = scope.scale_read_data( ch2_data, ch2gain, channel=2 )
    av1 = 0
    for value in ch1_scaled:
        av1 = av1 + value
        dc1 = dc1 + value
        rms1 = rms1 + (value*value)
    av1 = av1 / size
    av2 = 0
    for value in ch2_scaled:
        av2 = av2 + value
        dc2 = dc2 + value
        rms2 = rms2 + (value*value)
    av2 = av2 / size
    if downsample:
        capture.write( "{:<10.6g} {:< 10.4g} {:< 10.4g}\n".format( timestep, av1, av2 ) )
        timestep = timestep + tick * size
    else:
        for ch1_value, ch2_value in zip( ch1_scaled, ch2_scaled ): # merge CH1 & CH2
            capture.write( "{:<10.6g} {:< 10.4g} {:< 10.4g}\n".format( timestep, ch1_value, ch2_value ) )
            timestep = timestep + tick


# create file for time stamp and sample values of both channels
capture = open('captured.out'.format( sample_time ), 'wt')
skip1st = True # marker for skip of 1st (unstable) packet
tick = 1 / sample_rate
totalsize = 0
dc1 = dc2 = rms1 = rms2 = 0
timestep = 0
start_time = time.time() + scope.packetsize / sample_rate
end_time = start_time + sample_time
scope.start_capture()
shutdown_event = scope.read_async( packet_callback, scope.packetsize, outstanding_transfers=10, raw=True)

# sample until time is over
lastsec = -1
while True:
    to_go = start_time + sample_time - time.time()
    if int( to_go ) != lastsec:
        lastsec = int( to_go )
        sys.stderr.write( "\rCapture " + str(lastsec+1) + " seconds ...   " )
    if to_go <= 0:
        sys.stderr.write( "\rCaptured data for "+ str(sample_time) + " seconds\n" )
        break
    scope.poll()

scope.stop_capture()
shutdown_event.set()

# fetch remaining packets before closing the scope
time.sleep(1)
scope.close_handle()

dc1 = dc1 / totalsize
dc2 = dc2 / totalsize
rms1 = math.sqrt( rms1 / totalsize )
rms2 = math.sqrt( rms2 / totalsize )

print( "CH1: DC = {:8.4f} V, RMS = {:8.4f} V".format( dc1, rms1 ) )
print( "CH2: DC = {:8.4f} V, RMS = {:8.4f} V".format( dc2, rms2 ) )

capture.close()
