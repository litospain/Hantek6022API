#!/usr/bin/python3

__author__ = 'Robert Cope'

from PyHT6022.LibUsbScope import Oscilloscope
import sys
import time


'''
Program to calibrate offset and gain of 6022BE/BL
1.) Measure offset for the four gain steps x10, x5, x2, x1.
2. - 5.) Apply test voltages and measure the gain for the four gain steps
6.) Write a config file
'''


# average over 100ms @ 100kS/s -> 5 cycles @ 50 Hz or 6 cycles @ 60 Hz to cancel AC hum
def read_avg( voltage_range, sample_rate=10, samples = 12 * 1024 ):
	scope.set_sample_rate( sample_rate )
	scope.set_ch1_voltage_range(voltage_range)
	scope.set_ch2_voltage_range(voltage_range)
	time.sleep( 0.1 )
	ch1_data, ch2_data = scope.read_data( samples, raw=True, timeout=0)

	# skip first samples and keep 10000 
	skip = samples - 10000

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


print("Setting up scope...")

scope = Oscilloscope()
scope.setup()
scope.open_handle()

if (not scope.is_device_firmware_present):
	scope.flash_firmware()

scope.supports_single_channel = True

scope.set_num_channels( 2 )

# mV/div ranges
V_div = ( 10, 20, 50, 100, 200, 500, 1000, 2000, 5000 )
# corresponding amplifier gain settings
gains = ( 10, 10, 10,  10,   5,   2,    2,    1,    1 )
# available amplifier gains
gainID = ( 10, 5, 2, 1 )
# theoretical gain error of 6022 front end due to nominal resistor values (e.g. 5.1 kOhm instead 5.0)
error = ( 1.00, 1.01, 0.99, 0.99 )

# measure offset
# apply 0 V and measure the raw ADC values
print( "\nCalculate zero adjustment" )
input( "Apply 0 V to both channels and press <ENTER> " )

offset1 = {}
offset2 = {}

for gain in gainID:
	# average over 100 ms (cancel 50 Hz / 60 Hz)
	raw1, raw2 = read_avg( gain, 10 )
	offset1[ gain ] = 128 - raw1
	offset2[ gain ] = 128 - raw2

# measure gain
# apply a defined voltage, measure raw, correct offset and calculate gain
print( "\nCalculate gain adjustment"  )
print( "Apply the requested voltage (as exactly as possible) to both channels and press <ENTER>" )
print( "You can also apply a slightly lower or higher voltage and enter this value\n" )

gain1 = {}
gain2 = {}

index = 0 # index for gain error due to nominal resistor values
for gain in gainID:
	voltage = 4 / gain
	set = input( "Apply %4.2f V to both channels and press <ENTER> " % voltage )
	try:
		set = float( set ) # did the user supply an own voltage setting?
	except ValueError:
		set = voltage # else assume the proposed value 'voltage'
	# print( voltage/set )
	# we expect value 'target'
	target = error[ index ] * 100 * set / voltage
	index += 1
	# get offset error for gain setting & channel
	off1 = offset1[ gain ]
	off2 = offset2[ gain ]
	# read raw values
	raw1, raw2 = read_avg( gain, 10 ) # read @ 100kS/s
	# print( raw1, raw2 )
	# correct offset error
	value1 = raw1 + off1 - 128
	value2 = raw2 + off2 - 128
	# print( value1, value2 )
	# 
	if raw1 > 250 or value1 <= 0: # overdriven or negative input
		gain1[ gain ] = 1 # ignore setting, no correction
	else:
		gain1[ gain ] = target / value1 # corrective gain factor
	if raw2 > 250 or value2 <= 0: # same as for 1st channel
		gain2[ gain ] = 1
	else:
		gain2[ gain ] = target / value2


# write config file
configfile = "modelDSO6022.conf"
config = open( configfile, "w" )
config.write( ";OpenHantek calibration file for DSO6022\n;Created by tool 'calibrate.py'\n\n" )

# print( "[offset]" )
config.write( "[offset]\n" )

for index in range( len( gains ) ):
	gain = gains[ index ]
	volt = V_div[ index ]
	# print( "ch0\\%dmV=%d" % ( volt, offset1[ gain ] ) )
	# print( "ch1\\%dmV=%d" % ( volt, offset2[ gain ] ) )
	config.write( "ch0\\%dmV=%d\n" % ( volt, offset1[ gain ] ) )
	config.write( "ch1\\%dmV=%d\n" % ( volt, offset2[ gain ] ) )


# print( "[gain]" )
config.write( "\n[gain]\n" )

for index in range( len( gains ) ):
	gain = gains[ index ]
	volt = V_div[ index ]
	# print( "ch0\\%dmV=%6.4f" % ( volt, gain1[ gain ] ) )
	# print( "ch1\\%dmV=%6.4f" % ( volt, gain2[ gain ] ) )
	config.write( "ch0\\%dmV=%6.4f\n" % ( volt, gain1[ gain ] ) )
	config.write( "ch1\\%dmV=%6.4f\n" % ( volt, gain2[ gain ] ) )

config.close()

print( "\nReady, now install the configuration file '%s' into directory '~/.config/OpenHantek'\n" % configfile )
