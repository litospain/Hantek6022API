#!/usr/bin/python3

# flash the firmware from hex file

__author__ = 'Robert Cope'

from PyHT6022.LibUsbScope import Oscilloscope
from sys import argv

firmware = "firmware.hex"

if len( argv ) > 1:
	firmware = argv[ 1 ]
scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.flash_firmware_from_hex( firmware )
print( hex( scope.get_fw_version() ) )
scope.close_handle()
