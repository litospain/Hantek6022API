#!/usr/bin/python3
'''
Simple demo program that reads the output of 'capture_6022.py'
and creates the amplitude spectrum plots of both channels
It uses the extra python packages 'pandas' and 'matplotlib' 
for data analysis and visualisation. Install these packages with:
'apt install python3-matplotlib python3-pandas'
'''
 
import matplotlib.pyplot as plt
import pandas as pd

# Use output of 'capture_6022.py -o capture.csv' 
# Format: no header, values are SI units s and V, separated by comma
# The daa amount should be limited to a few seconds e.g. with '-t2'
capture = pd.read_csv('capture.csv', header=None)

# Separate it into three vectors
time = capture[0]
ch1  = capture[1]
ch2  = capture[2]

# Sample frequency
fs = 1 / (time[1] - time[0])

# Stack plots in two rows, one column, sync their frequency axes 
fig, axs = plt.subplots( 2, 1, sharex=True )

# Channel 1 spectrum (default window: hanning)
axs[0].magnitude_spectrum( ch1, fs, scale='dB' )
axs[0].grid( True )

# Channel 2 spectrum (default window: hanning)
axs[1].magnitude_spectrum( ch2, fs, scale='dB' )
axs[1].grid( True )

# And display everything
plt.show()
