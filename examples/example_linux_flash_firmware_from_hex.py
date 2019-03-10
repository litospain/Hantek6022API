#!/usr/bin/python3
# flash the default firmware -> PyHT6022.HantekFirmware.custom_firmware
# does not (yet) work wth OpenHantek project

__author__ = 'Robert Cope'

from PyHT6022.LibUsbScope import Oscilloscope
from sys import argv

if len( argv ) > 1:
	firmware = argv[ 1 ]

	scope = Oscilloscope()
	scope.setup()
	scope.open_handle()

	scope.flash_firmware_from_hex( firmware )

	scope.close_handle()

else:
	print( "usage: " + argv[0] + " hexfile" )
