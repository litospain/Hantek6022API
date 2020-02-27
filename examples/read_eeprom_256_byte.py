#!/usr/bin/python3

from PyHT6022.LibUsbScope import Oscilloscope

scope = Oscilloscope(0x14aa,0x0226)
scope.setup()
scope.open_handle()
eeprom = scope.read_eeprom( 0, 256 )
scope.close_handle()

f = open( "eeprom_256.dat", "wb" )
f.write( eeprom )
f.close()

print( eeprom )
