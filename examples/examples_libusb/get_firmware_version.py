#!/usr/bin/python3

__author__ = 'Robert Cope'
"""
"""

from PyHT6022.LibUsbScope import Oscilloscope

scope = Oscilloscope()
scope.setup()
scope.open_handle()
print( hex( scope.get_fw_version() ) )
scope.close_handle()
