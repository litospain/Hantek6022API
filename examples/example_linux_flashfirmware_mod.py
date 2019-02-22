#!/usr/bin/python3
# Flash the modded firmware that is also used by OpenHantek project

__author__ = 'Robert Cope'

from PyHT6022.LibUsbScope import Oscilloscope
from PyHT6022.HantekFirmware import mod_firmware_01

scope = Oscilloscope()
scope.setup()
scope.open_handle()

scope.flash_firmware( mod_firmware_01 )

scope.close_handle()
