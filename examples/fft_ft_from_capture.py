#!/usr/bin/python3

'''
Simple demo program that reads the output of 'capture_6022.py'
and creates the amplitude spectrum plots of both channels
It uses the extra python package 'matplotlib'
for data analysis and visualisation. Install with:
'apt install python3-matplotlib'
it has also an example how to define an own windowing function
'''

import csv
import math
import matplotlib.pyplot as plt
import sys

# Use output of 'capture_6022.py'
# Format: no header, values are SI units s and V, separated by comma
# The data amount should be limited to a few seconds,
# e.g. with '-t2' or with downsampling for slowly changing signals

if len( sys.argv ) > 1:
    infile = open( sys.argv[1], 'r' )
else:
    infile = sys.stdin

capture = csv.reader( infile )

# separate into three lists
time, ch1, ch2 = [], [], []
for row in capture:
    time.append( float( row[0] ) )
    # scale to dbV:
    # multiply by 2 because we use only half of the spectrum ...
    # ... then divide by sqrt(2) to scale to rms ...
    # ... and finally multiply by 1.16 to compensate 1.3 dB loss of flat_top
    ch1.append( float( row[1] ) * 1.64 )
    ch2.append( float( row[2] ) * 1.64 )

infile.close()

# Sample frequency
fs = 1 / (time[1] - time[0])


##############################
# define own window function #
##############################
#
def flat_top( x ):
    N = len( x )
    # use matlab coefficients -> https://www.mathworks.com/help/signal/ref/flattopwin.html
    # scaled by 1/0.21547095 to get an overall window amplitude gain of 1.0
    a0, a1, a2, a3, a4 = 1, 1.933732403, 1.286777443, 0.387889630, 0.032242713
    p = 2 * math.pi / (N-1)
    # gain = 0
    for n in range( N ):
        x[n] = (
            a0
          - a1 * math.cos( p * n )
          + a2 * math.cos( p * n * 2 )
          - a3 * math.cos( p * n * 3 )
          + a4 * math.cos( p * n * 4 )
        )
        # gain += x[n]
    # print( "flat_top:", gain/N )
    return x
#
##############################


# Stack plots in two rows, one column, sync their frequency axes
fig, axs = plt.subplots( 2, 1, sharex = True )

# Channel 1 spectrum
axs[0].magnitude_spectrum( ch1, fs, scale = 'dB', window = flat_top )
axs[0].grid( True )

# Channel 2 spectrum
axs[1].magnitude_spectrum( ch2, fs, scale = 'dB', window = flat_top )
axs[1].grid( True )

# And display everything
plt.show()
