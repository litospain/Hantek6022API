#!/usr/bin/python3

'''
Simple demo program that reads the output of 'capture_6022.py'
and creates the amplitude spectrum plots of both channels.
It uses the extra python package 'matplotlib' for visualisation.
Install with: 'apt install python3-matplotlib' if missing.
'''

import csv
import matplotlib.pyplot as plt
import sys

# Use output of 'capture_6022.py'
# Format: no header, values are SI units s and V, separated by comma
# The data amount should be limited to a few seconds
# e.g. with '-t2' or by downsampling for slowly changing signals

if len( sys.argv ) > 1: # if called with an arg take this as filename
    infile = open( sys.argv[1], 'r' )
else: # else use stdin
    infile = sys.stdin

# process the csv data
capture = csv.reader( infile )

# separate into three lists
time, ch1, ch2 = [], [], []
for row in capture:
    time.append( float( row[0] ) )
    ch1.append( float( row[1] ) )
    ch2.append( float( row[2] ) )

infile.close()

# Stack plots in two rows, one column, sync their frequency axes
fig, axs = plt.subplots( 2, 1, sharex = True )

# Channel 1
axs[0].plot( time, ch1 )
axs[0].grid( True )

# Channel 2
axs[1].plot( time, ch2 )
axs[1].grid( True )

# And display everything
plt.show()
