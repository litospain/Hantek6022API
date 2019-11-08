#!/usr/bin/python3

__author__ = 'Jochen Hoenicke'

from PyHT6022.LibUsbScope import Oscilloscope

scope = Oscilloscope()
scope.setup()
scope.open_handle()
eeprom = scope.read_eeprom(0, 8)
scope.close_handle()

f = open( "eeprom.dat", "wb" )
f.write( eeprom )
f.close()

print( eeprom )
