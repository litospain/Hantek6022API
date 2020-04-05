# About the firmware
The 6022BE (and 6022BL) has only limited persistent storage so the firmware must be uploaded to the device's RAM
every time the oscilloscope is powered up.
The dump of the packet transfer to the 6022BE was captured by [Robert](https://github.com/rpcope1/Hantek6022API)
and is given as `firmware_packet_dump.csv` and was used by him to build the **stock_firmware** in this module.

This stock version was later analysed and improved by [Jochen](https://github.com/jhoenicke/Hantek6022API)
and Robert to create the two **mod_firmware** versions.
Without source code this was a not so easy task - good work!
If you're interested in the details read the huge EEVBLOG thread, this is a
[good starting point](https://www.eevblog.com/forum/testgear/hantek-6022be-20mhz-usb-dso/msg656059/#msg656059).

The **custom firmware** (BE & BL) is based on fx2lib code. The latest version also allows reading/writing of EEPROMs
and thus has all features like the stock and modded versions and allows an easy implementation of new features.
The digital storage oscilloscope program **OpenHantek6022** from https://github.com/OpenHantek/OpenHantek6022
already uses this custom FW.

Provided are different FW flavours as part of the python package:

| **Name**           | **Path**                     | **Comment**                                                      |
|--------------------|------------------------------|------------------------------------------------------------------|
| stock_firmware     | stock/stock_fw.ihex          | Firmware that was originally uploaded to the device by vendor SW |
| mod_firmware_01    | modded/mod_fw_01.ihex        | Patched stock firmware with sample rate and stability improvements |
| mod_firmware_iso   | modded/mod_fw_iso.ihex       | Patched stock firmware that allows isochronous transfer (instead of bulk) |
| custom_firmware_BE | DSO6022BE/dso6022be-firmware.hex | backported from sigrok-fw |
| custom_firmware_BL | DSO6022BL/dso6022bl-firmware.hex | backported from sigrok-fw |

Default:
    default_firmware = custom_firmware = custom_firmware_BE

