#!/usr/bin/python3

__author__ = 'Robert Cope'

from PyHT6022.LibUsbScope import Oscilloscope
import sys


'''
NOT YET WOKING
Program to calibrate offset and gain of 6022BE/BL
1.) Measure offset for gain steps x10, x5, x2, x1 at low (<30 MS/s) and high (>= 30 MS/s) speed
2.) Apply a test voltage and measure the gain for the four gain steps
'''


def read_avg( voltage_range, sample_rate=10, samples = 10240 ):
	skip = 2048 # skip first samples
	scope.set_sample_rate( sample_rate )
	scope.set_ch1_voltage_range(voltage_range)
	scope.set_ch2_voltage_range(voltage_range)
	ch1_data, ch2_data = scope.read_data( samples+skip, raw=True, timeout=0)

	# print( len( ch1_data), len( ch2_data ) )

	sum = 0
	iii = 0
	for sample in ch1_data[skip:]:
		sum += sample
		iii += 1
	avg1 = int( 0.5 + sum / iii )

	sum = 0
	iii = 0
	for sample in ch2_data[skip:]:
		sum += sample
		iii += 1
	avg2 = int( 0.5 + sum / iii )

	return ( avg1, avg2 )



scope = Oscilloscope()
scope.setup()
scope.open_handle()

if (not scope.is_device_firmware_present):
	scope.flash_firmware()

scope.supports_single_channel = True

print("Setting up scope!")

scope.set_num_channels( 2 )

offset = []

for sample_rate in ( 1, 30 ):


	for voltage_range in ( 10, 5, 2, 1 ):
		avg1, avg2 = read_avg( voltage_range, sample_rate )

		print( sample_rate, voltage_range, avg1, avg2, sep='\t' )

		offset.append( avg1 )
		offset.append( avg2 )

print( offset )


i1 = 0
for gain in ( 10, 5, 2, 1 ):

	voltage = 4 / gain
	input( 'set voltage (max %4.2f V) ' % voltage )
	i2 = 0
	for sample_rate in ( 1, 30 ):
		o1 = offset[ i1 + i2 ]
		o2 = offset[ i1 + i2 + 1 ]
		scope.set_sample_rate( sample_rate )

		val1, val2 = read_avg( voltage_range, sample_rate )

		print( i1+i2, (val1-o1), (val2-o2) )
		
		i2 += 8

	i1 += 2


scope.close_handle()
