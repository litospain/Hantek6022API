all: fw_custom

fw_custom:
	cd PyHT6022/HantekFirmware/custom && make

install:
	python3 setup.py install
	cp 60-hantek-6022-usb.rules /etc/udev/rules.d/

deb:
	checkinstall --requires python3-libusb1 --install=no

clean:
	-rm backup-*.tgz
	-rm *~ .*~
