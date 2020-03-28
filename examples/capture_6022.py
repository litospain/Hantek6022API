#!/usr/bin/python3
'''
Samples CH1 and Ch2 for a defined time and writes the time stamp and the voltage values to a file

usage: capture_6022.py [-h] [-d DOWNSAMPLE] [-o OUTFILE] [-r RATE] [-t TIME]
                       [-x CH1] [-y CH2]

optional arguments:
  -h, --help            show this help message and exit
  -d, --downsample DOWNSAMPLE
                        downsample 256 x DOWNSAMPLE
  -o OUTFILE, --outfile OUTFILE
                        write the data into OUTFILE
  -r RATE, --rate RATE  sample rate in kS/s (20, 50, 64, 100, default: 20)
  -t TIME, --time TIME  capture time in seconds (default: 1.0)
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
ap.add_argument( "-d", "--downsample", type = int, default = 0,
    help="downsample 256 x DOWNSAMPLE" )
ap.add_argument( "-o", "--outfile", type = argparse.FileType("w"),
    help="write the data into OUTFILE" )
ap.add_argument( "-r", "--rate", type = int, default = 20,
    help="sample rate in kS/s (20, 50, 64, 100, default: 20)" )
ap.add_argument( "-t", "--time", type = float, default = 1,
    help="capture time in seconds (default: 1.0)" )
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
    print( "error, ch1 gain must be one of:", valid_gains )
    argerror = True
if ch2gain not in valid_gains:
    print( "error, ch2 gain must be one of:", valid_gains )
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


##########################################################
# this callback is called every time a data packet arrives
# scale the data packets and write them into the outfile
#
def pcb( ch1_data, ch2_data ):
    # define "static" variables
    if 'av1' not in pcb.__dict__:
        pcb.av1 = 0
    if 'av2' not in pcb.__dict__:
        pcb.av2 = 0
    if 'timestep' not in pcb.__dict__:
        pcb.timestep = 0
    if 'slowdown' not in pcb.__dict__:
        pcb.slowdown = 0

    global skip1st, start_time, tick
    global totalsize, dc1, dc2, rms1, rms2

    size = len( ch1_data )
    if( size == 0 ):
        return
    if skip1st: # skip the 1st (unstable) block
        skip1st = False
        return
    totalsize = totalsize + size
    ch1_scaled = scope.scale_read_data( ch1_data, ch1gain, channel=1 )
    ch2_scaled = scope.scale_read_data( ch2_data, ch2gain, channel=2 )
    # average over the block (256 byte), prepare AC/DC
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
    if downsample: # average further over more blocks
        pcb.av1 = pcb.av1 + av1
        pcb.av2 = pcb.av2 + av2
        pcb.slowdown = pcb.slowdown + 1
        if pcb.slowdown >= downsample:
            pcb.slowdown = 0
            pcb.av1 = pcb.av1 / downsample
            pcb.av2 = pcb.av2 / downsample
            if pcb.timestep < sample_time:
                outfile.write( "{:<10.6g}, {:< 10.4g}, {:< 10.4g}\n".format( pcb.timestep, pcb.av1, pcb.av2 ) )
            pcb.av1 = pcb.av2 = 0
            pcb.timestep = pcb.timestep + tick * size * downsample
    else: # write out every sample
        for ch1_value, ch2_value in zip( ch1_scaled, ch2_scaled ): # merge CH1 & CH2
            if pcb.timestep < sample_time:
                outfile.write( "{:<10.6g}, {:< 10.4g}, {:< 10.4g}\n".format( pcb.timestep, ch1_value, ch2_value ) )
            pcb.timestep = pcb.timestep + tick
#
##########################################################


skip1st = True # marker for skip of 1st (unstable) packet
tick = 1 / sample_rate # time between two samples
totalsize = 0
dc1 = dc2 = rms1 = rms2 = 0

timestep = 0
start_time = time.time() + scope.packetsize / sample_rate # correct the 1st skipped block

# GO!
scope.start_capture()
shutdown_event = scope.read_async( pcb, scope.packetsize, outstanding_transfers=10, raw=True)

# sample until time is over, show the progress
lastsec = None
while True:
    to_go = start_time + sample_time - time.time()
    if to_go <=  - downsample * 256 * tick:
        break
    if int( to_go ) != lastsec:
        if None == lastsec:
            sys.stderr.write( "\rCapturing " + str(sample_time) + " seconds ...    " )
        elif lastsec > 0:
            sys.stderr.write( "\rCapturing " + str(lastsec) + " seconds ...    " )
        else:
            sys.stderr.write( "\rCapturing ...              " )
        lastsec = int( to_go )
        outfile.flush()
    scope.poll()

# STOP!
scope.stop_capture()
shutdown_event.set()

# fetch remaining packets before closing the scope (max 1024 * 50µs = 0.0512 s)
time.sleep(0.1)
scope.close_handle()

if downsample: # calculate the effective sample rate
    sample_rate = sample_rate / 256 / downsample
sys.stderr.write( "\rCaptured data for {} second(s) @ {} S/s\n".format( sample_time, sample_rate) )

# average of all samples (DC)
dc1 = dc1 / totalsize
dc2 = dc2 / totalsize
# average of all samples² (RMS² = DC² + AC²)
rms1 = rms1 / totalsize
rms2 = rms2 / totalsize
# sqrt of AC² (AC)
ac1 = math.sqrt( rms1 - dc1 * dc1 )
ac2 = math.sqrt( rms2 - dc2 * dc2 )
# sqrt of RMS² (RMS)
rms1 = math.sqrt( rms1 )
rms2 = math.sqrt( rms2 )

sys.stderr.write( "CH1: DC = {:8.4f} V, AC = {:8.4f} V, RMS = {:8.4f} V\n".format( dc1, ac1, rms1 ) )
sys.stderr.write( "CH2: DC = {:8.4f} V, AC = {:8.4f} V, RMS = {:8.4f} V\n".format( dc2, ac2, rms2 ) )

outfile.close()
