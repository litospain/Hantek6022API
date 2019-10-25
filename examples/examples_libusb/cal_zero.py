#!/usr/bin/python3

'''
Program to calibrate offset of 6022BE/BL
1.) Measure offset at low and high speed for the four gain steps x10, x5, x2, x1
2.) Write offset values into eeprom
'''

from PyHT6022.LibUsbScope import Oscilloscope
import sys
import time
import binascii


# average over 100ms @ 100kS/s -> 5 cycles @ 50 Hz or 6 cycles @ 60 Hz to cancel AC hum
def read_avg( voltage_range, sample_rate=110, repeat = 1, samples = 12 * 1024 ):
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

#	avg1 = int( 0.5 + sum1 / count1 )
#	avg2 = int( 0.5 + sum2 / count2 )
	avg1 = sum1 / count1
	avg2 = sum2 / count2

	return ( avg1, avg2 )


print("Setting up scope...")

scope = Oscilloscope()
scope.setup()
scope.open_handle()

if (not scope.is_device_firmware_present):
	scope.flash_firmware()

scope.supports_single_channel = True

scope.set_num_channels( 2 )

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
offset_1 = {}
offset_2 = {}
offhi1 = {}
offhi2 = {}
offhi_1 = {}
offhi_2 = {}



for gain in gainSteps:
	# average 10 times over 100 ms (cancel 50 Hz / 60 Hz)
	print( "Measure offset at low speed for gain ", gain )
	fine1, fine2 = read_avg( gain, 110, 10 )
	#print( fine1, fine2 )
	raw1 = int( fine1 + 0.5 )
	fine1 = int( 128.5 + (fine1 - raw1) * 250.0 )
	raw2 = int( fine2 + 0.5 )
	fine2 = int( 128.5 + (fine2 - raw2) * 250.0 )
	#print( raw1, fine1, raw2, fine2 )
	offset1[ gain ] = raw1
	offset_1[ gain ] = fine1
	offset2[ gain ] = raw2
	offset_2[ gain ] = fine2
	print( "Measure offset at high speed for gain ", gain )
	fine1, fine2 = read_avg( gain, 30, 10 )
	raw1 = int( fine1 + 0.5 )
	fine1 = int( 128.5 + (fine1 - raw1) * 250.0 )
	raw2 = int( fine2 + 0.5 )
	fine2 = int( 128.5 + (fine2 - raw2) * 250.0 )
	#print( raw1, fine1, raw2, fine2 )
	offhi1[ gain ] = raw1
	offhi_1[ gain ] = fine1
	offhi2[ gain ] = raw2
	offhi_2[ gain ] = fine2

ee_offset = bytearray( scope.get_calibration_values( 32 + 16 + 32 ) )

for index, gainID in enumerate( gains ):
	# print( gains[index], offset1[gainID], offset2[gainID], offhi1[gainID], offhi2[gainID],  )
	# prepare eeprom content
	ee_offset[ 2 * index ] = offset1[ gainID ] 		# CH1 offset integer part
	ee_offset[ 2 * index + 48 ] = offset_1[ gainID ]	# CH1 offset fractional part
	ee_offset[ 2 * index + 1 ] = offset2[ gainID ]		# CH2 offset integer part
	ee_offset[ 2 * index + 49 ] = offset_2[ gainID ]	# CH2 offset fractional part
	ee_offset[ 2 * index + 16 ] = offhi1[ gainID ]		# same for CH2
	ee_offset[ 2 * index + 64 ] = offhi_1[ gainID ]		#
	ee_offset[ 2 * index + 17 ] = offhi2[ gainID ]		#
	ee_offset[ 2 * index + 65 ] = offhi_2[ gainID ]		#

print( "eeprom content [  8 .. 40 ]: ", binascii.hexlify( ee_offset[  0:32 ] ) )
print( "eeprom content [ 40 .. 56 ]: ", binascii.hexlify( ee_offset[ 32:48 ] ) )
print( "eeprom content [ 56 .. 88 ]: ", binascii.hexlify( ee_offset[ 48:80 ] ) )


scope.set_calibration_values( ee_offset )

scope.close_handle()
