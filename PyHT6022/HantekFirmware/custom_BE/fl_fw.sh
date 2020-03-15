#!/bin/sh

flash_firmware_from_hex.py build/dso6022be-firmware.hex
../../../examples/get_firmware_version.py

