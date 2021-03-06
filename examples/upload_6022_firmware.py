#!/usr/bin/python3

__author__ = 'Robert Cope'
"""
Flash default firmware into device
either firmareBE or firmwareBL
depending on VID/PID
"""

from PyHT6022.LibUsbScope import Oscilloscope

scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.flash_firmware()
print( hex( scope.get_fw_version() ) )
scope.close_handle()
