#!/usr/bin/python3

__author__ = 'Robert Cope'

from PyHT6022.LibUsbScope import Oscilloscope
from PyHT6022.HantekFirmware import mod_firmware_iso as Firmware

scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.flash_firmware( firmware = Firmware )
scope.close_handle()
