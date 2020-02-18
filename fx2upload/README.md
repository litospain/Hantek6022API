Quick hack to upload an intel hex firmware file on a cypress fx2 device.

    usage: fx2hexload [OPTIONS] FIRMWARE [VID PID]
      uploads firmware to a Cypress FX2 USB device identified by VID and PID
      OPTIONS:   -v verbose
      FIRMWARE:  intel hex file
      VID:       VendorID as hex value, default =  0x04B4
      PID:       ProductID as hex value, default = 0x8613
