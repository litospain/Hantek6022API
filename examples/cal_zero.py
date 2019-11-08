#!/usr/bin/python3

# DEPRECATED: Use calibrate.py -e

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

    # measured values are 0x80 binary offset -> 0V = 0x80
    avg1 = sum1 / count1 - 0x80
    avg2 = sum2 / count2 - 0x80

    return ( avg1, avg2 )


print("Setting up scope...")

scope = Oscilloscope()
scope.setup()
scope.open_handle()

if (not scope.is_device_firmware_present):
    scope.flash_firmware()

scope.supports_single_channel = True

# select two channels
scope.set_num_channels( 2 )
# set coupling of both channels to DC
scope.set_ch1_ch2_ac_dc( scope.DC_DC )

# corresponding amplifier gain settings
gains = ( 10, 10,  10,   5,   2,    1,    1,    1 )
# available amplifier gains
gainSteps = ( 10, 5, 2, 1 )
# theoretical gain error of 6022 front end due to nominal resistor values (e.g. 5.1 kOhm instead 5.0)
error = ( 1.00, 1.01, 0.99, 0.99 )


# measure offset
# apply 0 V and measure the ADC values
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
    value1, value2 = read_avg( gain, 110, 10 )
    #print( fine1, fine2 )
    raw1 =  int( round( value1 ) )
    fine1 = int( round( (value1 - raw1) * 250.0 ) )
    raw2 =  int( round( value2 ) )
    fine2 = int( round( (value2 - raw2) * 250.0 ) )
    #print( raw1, fine1, raw2, fine2 )
    offset1[ gain ] = raw1
    offset_1[ gain ] = fine1
    offset2[ gain ] = raw2
    offset_2[ gain ] = fine2
    print( "Measure offset at high speed for gain ", gain )
    value1, value2 = read_avg( gain, 30, 10 )
    #print( fine1, fine2 )
    raw1 =  int( round( value1 ) )
    fine1 = int( round( (value1 - raw1) * 250.0 ) )
    raw2 =  int( round( value2 ) )
    fine2 = int( round( (value2 - raw2) * 250.0 ) )
    #print( raw1, fine1, raw2, fine2 )
    offhi1[ gain ] = raw1
    offhi_1[ gain ] = fine1
    offhi2[ gain ] = raw2
    offhi_2[ gain ] = fine2


# get calibration values stored in the scope (all values are 0x80 binary offset, 0x80 = 0)
# use these values as default if new values are not plausible
# structure and representation of these values due to historical reason
# 32 byte integer offset CH1, CH2,... for 8 input ranges (20mV, 50mV,..., 5V) for low and high speed
# these are also the factory calibration settings (0x80 = no offset)
# next 16 bytes are the gain correction values CH1, CH2, ... same voltage range, only one speed
# 0x80 = 1.0, 0x80-125 = 0.75, 0x80+125 = 1.25
# next 32 bytes are the fractional error (range -0.5 ... +0.5) of the offset values above,
# 0x80 = 0, 0x80-125 = -0.5, 0x80+125 = +0.5
#
ee_offset = bytearray( scope.get_calibration_values( 32 + 16 + 32 ) )


for index, gainID in enumerate( gains ):
    # print( gains[index], offset1[gainID], offset2[gainID], offhi1[gainID], offhi2[gainID],  )
    # prepare eeprom content
    if ( abs( offset1[ gainID ] ) <= 25 ):                      # offset too high -> skip
        ee_offset[ 2 * index ] = 0x80 + offset1[ gainID ]       # CH1 offset integer part
    if ( abs( offset_1[ gainID ] ) <= 125 ):                    # frac part not plausible
        ee_offset[ 2 * index + 48 ] = 0x80 + offset_1[ gainID ] # CH1 offset fractional part
    if ( abs( offset2[ gainID ] ) <= 25 ):
        ee_offset[ 2 * index + 1 ] = 0x80 + offset2[ gainID ]   # CH2 offset integer part
    if ( abs( offset_2[ gainID ] ) <= 125 ):
        ee_offset[ 2 * index + 49 ] = 0x80 + offset_2[ gainID ] # CH2 offset fractional part
    if ( abs( offhi1[ gainID ] ) <= 25 ):
        ee_offset[ 2 * index + 16 ] = 0x80 + offhi1[ gainID ]   # same for CH2
    if ( abs( offhi_1[ gainID ] ) <= 125 ):
        ee_offset[ 2 * index + 64 ] = 0x80 + offhi_1[ gainID ]  #
    if ( abs( offhi2[ gainID ] ) <= 25 ):
        ee_offset[ 2 * index + 17 ] = 0x80 + offhi2[ gainID ]   #
    if ( abs( offhi_2[ gainID ] ) <= 125 ):
        ee_offset[ 2 * index + 65 ] = 0x80 + offhi_2[ gainID ]  #

print( "eeprom content [  8 .. 40 ]: ", binascii.hexlify( ee_offset[  0:32 ] ) )
print( "eeprom content [ 40 .. 56 ]: ", binascii.hexlify( ee_offset[ 32:48 ] ) )
print( "eeprom content [ 56 .. 88 ]: ", binascii.hexlify( ee_offset[ 48:80 ] ) )


# scope.set_calibration_values( ee_offset )

scope.close_handle()
