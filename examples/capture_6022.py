#!/usr/bin/python3
'''
Samples CH1 and Ch2 for a defined time and writes the time stamp and the voltage values to a file

usage: capture_6022.py [-h] [-d] [-o [OUTFILE]] [-r RATE] [-t TIME] [-x CH1]
                       [-y CH2]

optional arguments:
  -h, --help            show this help message and exit
  -d, --downsample      downsample 256x
  -o [OUTFILE], --outfile [OUTFILE]
                        write the data into [OUTFILE]
  -r RATE, --rate RATE  sample rate in kS/s (20, 50, 64, 100, default: 20)
  -t TIME, --time TIME  capture time in seconds (default: 60)
  -x CH1, --ch1 CH1     gain of channel 1 (1, 2, 5, 10, default: 1)
  -y CH2, --ch2 CH2     gain of channel 2 (1, 2, 5, 10, default: 1)
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
ap.add_argument( "-o", "--outfile", type = argparse.FileType("w"), nargs = "?",
    help="write the data into [OUTFILE]" )
ap.add_argument( "-r", "--rate", type = int, default = 20,
    help="sample rate in kS/s (20, 50, 64, 100, default: 20)" )
ap.add_argument( "-t", "--time", type = float, default = 60,
    help="capture time in seconds (default: 60.0)" )
ap.add_argument( "-x", "--ch1", type = int, default = 1,
    help="gain of channel 1 (1, 2, 5, 10, default: 1)" )
ap.add_argument( "-y", "--ch2", type = int, default = 1,
    help="gain of channel 2 (1, 2, 5, 10, default: 1)" )

options = ap.parse_args()

############
# settings #
############
#
channels    = 2
downsample  = options.downsample
sample_rate = options.rate
sample_time = options.time
ch1gain     = options.ch1
ch2gain     = options.ch2
outfile     = options.outfile or sys.stdout

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


########################################################
# this callback is called every time data packet arrives
# scale the data packets and write them into the file
#
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
        if timestep <= sample_time:
            outfile.write( "{:<10.6g} {:< 10.4g} {:< 10.4g}\n".format( timestep, av1, av2 ) )
        timestep = timestep + tick * size
    else:
        for ch1_value, ch2_value in zip( ch1_scaled, ch2_scaled ): # merge CH1 & CH2
            if timestep <= sample_time:
                outfile.write( "{:<10.6g} {:< 10.4g} {:< 10.4g}\n".format( timestep, ch1_value, ch2_value ) )
            timestep = timestep + tick
#
########################################################


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
lastsec = 0
while True:
    to_go = start_time + sample_time - time.time()
    if to_go <= 0:
        break
    if int( to_go ) != lastsec:
        if lastsec:
            sys.stderr.write( "\rCapturing " + str(lastsec) + " seconds ...   " )
        else:
            sys.stderr.write( "\rCapturing " + str(sample_time) + " seconds ...   " )
        lastsec = int( to_go )
        outfile.flush()
    scope.poll()

scope.stop_capture()
shutdown_event.set()

# fetch remaining packets before closing the scope (max 1024 * 50µs = 0.0512 s)
time.sleep(0.1)

scope.close_handle()
sys.stderr.write( "\rCaptured data for "+ str(sample_time) + " second(s)\n" )

dc1 = dc1 / totalsize
dc2 = dc2 / totalsize
rms1 = math.sqrt( rms1 / totalsize )
rms2 = math.sqrt( rms2 / totalsize )

sys.stderr.write( "CH1: DC = {:8.4f} V, RMS = {:8.4f} V\n".format( dc1, rms1 ) )
sys.stderr.write( "CH2: DC = {:8.4f} V, RMS = {:8.4f} V\n".format( dc2, rms2 ) )

outfile.close()
