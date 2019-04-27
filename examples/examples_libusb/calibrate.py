#!/usr/bin/python3

'''
Program to calibrate offset and gain of 6022BE/BL
1.) Measure offset at low and high speed for the four gain steps x10, x5, x2, x1
2. - 5.) Apply test voltages and measure the gain for the four gain steps
6.) Write a config file
7.) Write data into eeprom
'''

from PyHT6022.LibUsbScope import Oscilloscope
import sys
import time
import binascii


# average over 100ms @ 100kS/s -> 5 cycles @ 50 Hz or 6 cycles @ 60 Hz to cancel AC hum
def read_avg( voltage_range, sample_rate=10, repeat = 1, samples = 12 * 1024 ):
	scope.set_sample_rate( sample_rate )
	scope.set_ch1_voltage_range(voltage_range)
	scope.set_ch2_voltage_range(voltage_range)
	time.sleep( 0.1 )
	
	sum1 = 0
	sum2 = 0
	count1 = 0
	count2 = 0

	for rep in range( repeat ): # repeat measurement
		ch1_data, ch2_data = scope.read_data( samples, raw=True, timeout=0)

		# skip first samples and keep 10000 
		skip = samples - 10000

		# print( len( ch1_data), len( ch2_data ) )

		for sample in ch1_data[skip:]:
			sum1 += sample
			count1 += 1

		for sample in ch2_data[skip:]:
			sum2 += sample
			count2 += 1

	avg1 = int( 0.5 + sum1 / count1 )
	avg2 = int( 0.5 + sum2 / count2 )

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
V_div = ( 20, 50, 100, 200, 500, 1000, 2000, 5000 )
# corresponding amplifier gain settings
gains = ( 10, 10,  10,   5,   2,    1,    1,    1 )
# available amplifier gains
gainSteps = ( 10, 5, 2, 1 )
# theoretical gain error of 6022 front end due to nominal resistor values (e.g. 5.1 kOhm instead 5.0)
error = ( 1.00, 1.01, 0.99, 0.99 )


# measure offset
# apply 0 V and measure the raw ADC values
print( "\nCalculate zero adjustment" )
input( "Apply 0 V to both channels and press <ENTER> " )

offset1 = {}
offset2 = {}
offhi1 = {}
offhi2 = {}

for gain in gainSteps:
	# average 10 times over 100 ms (cancel 50 Hz / 60 Hz)
	print( "Measure offset at low speed for gain ", gain )
	raw1, raw2 = read_avg( gain, 10, 10 )
	offset1[ gain ] = 0x80 - raw1
	offset2[ gain ] = 0x80 - raw2
	print( "Measure offset at high speed for gain ", gain )
	raw1, raw2 = read_avg( gain, 30, 10 )
	offhi1[ gain ] = 0x80 - raw1
	offhi2[ gain ] = 0x80 - raw2


ee_offset = bytearray( 32 )

# create config file
configfile = "modelDSO6022.conf"
config = open( configfile, "w" )
config.write( ";OpenHantek calibration file for DSO6022\n;Created by tool 'calibrate.py'\n\n" )

config.write( "[offset]\n" )

for index, gainID in enumerate( gains ):
	voltID = V_div[ index ]
	config.write( "ch0\\%dmV=%d\n" % ( voltID, offset1[ gainID ] ) )
	config.write( "ch1\\%dmV=%d\n" % ( voltID, offset2[ gainID ] ) )
	# prepare eeprom content
	ee_offset[ 2 * index ] = 0x80 - offset1[ gainID ]
	ee_offset[ 2 * index + 1 ] = 0x80 - offset2[ gainID ]
	ee_offset[ 2 * index + 16 ] = 0x80 - offhi1[ gainID ]
	ee_offset[ 2 * index + 17 ] = 0x80 - offhi2[ gainID ]

print( "eeprom content [ 8 .. 39 ]: ", binascii.hexlify(ee_offset) )


# measure gain
# apply a defined voltage, measure raw, correct offset and calculate gain
print( "\nCalculate gain adjustment"  )
print( "Apply the requested voltage (as exactly as possible) to both channels and press <ENTER>" )
print( "You can also apply a slightly lower or higher voltage and enter this value\n" )

gain1 = {}
gain2 = {}

index = 0 # index for gain error due to nominal resistor values
for gain in gainSteps:
	voltage = 4 / gain
	setpoint = input( "Apply %4.2f V to both channels and press <ENTER> " % voltage )
	try:
		setpoint = float( setpoint ) # did the user supply an own voltage setting?
	except ValueError:
		setpoint = voltage # else assume the proposed value 'voltage'
	# we expect value 'target'
	target = error[ index ] * 100 * setpoint / voltage
	index += 1
	# get offset error for gain setting & channel
	off1 = offset1[ gain ]
	off2 = offset2[ gain ]
	# read raw values, average over 10 times 100 ms
	raw1, raw2 = read_avg( gain, 10, 10 ) # read @ 100kS/s
	# print( raw1, raw2 )
	# correct offset error
	value1 = raw1 + off1 - 0x80
	value2 = raw2 + off2 - 0x80
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


ee_gain = bytearray( 16 )

config.write( "\n[gain]\n" )

for index, gainID in enumerate( gains ):
	voltID = V_div[ index ]
	g1 = gain1[ gainID ]
	g2 = gain2[ gainID ]
	config.write( "ch0\\%dmV=%6.4f\n" % ( voltID, g1 ) )
	config.write( "ch1\\%dmV=%6.4f\n" % ( voltID, g2 ) )
        # convert double 0.75 ... 1.25 -> byte 0x80-125 ... 0x80+125
	ee_gain[ 2 * index ] = int( ( g1 - 1 ) * 500 + 0x80 + 0.5 )
	ee_gain[ 2 * index + 1 ] = int( ( g2 - 1 ) * 500 + 0x80 + 0.5 )

config.close()

print( "eeprom gain content [ 40 .. 55 ]: ", ee_gain )

scope.set_calibration_values( ee_offset + ee_gain )

scope.close_handle()

print( "\nReady, now install the configuration file '%s' into directory '~/.config/OpenHantek'\n" % configfile )
