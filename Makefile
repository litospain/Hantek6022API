all: fw_custom_BE fw_custom_BL

fw_custom_BE:
	cd PyHT6022/HantekFirmware/custom_BE && make

fw_custom_BL:
	cd PyHT6022/HantekFirmware/custom_BL && make

install:
	python3 setup.py install
	cp 60-hantek-6022-usb.rules /etc/udev/rules.d/

deb:
	fakeroot checkinstall --requires python3-libusb1 --install=no --backup=no --deldoc=yes

clean:
	-rm *~ .*~
