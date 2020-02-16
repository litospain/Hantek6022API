#!/usr/bin/python3

__author__ = 'Jochen Hoenicke'

from PyHT6022.LibUsbScope import Oscilloscope


scope = Oscilloscope()
scope.setup()
scope.open_handle()

# read at end-16, 16 bytes
eeprom = scope.read_eeprom( 256 - 16, 16 )

# write at end-16
scope.write_eeprom( 256 - len( eeprom ), eeprom )
scope.close_handle()

print( eeprom )
