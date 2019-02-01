all: fw_custom

fw_custom:
	cd PyHT6022/HantekFirmware/custom && make

install:
	python3 setup.py install

deb:
	checkinstall --requires python3-libusb1
