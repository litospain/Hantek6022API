all: fw_custom_BE fw_custom_BL

BE=PyHT6022/HantekFirmware/custom_BE
BL=PyHT6022/HantekFirmware/custom_BL
BEb=$(BE)/build
BLb=$(BL)/build

fw_custom_BE:
	cd $(BE) && make

fw_custom_BL:
	cd $(BL) && make

install: all
	python3 setup.py install
	cp 60-hantek-6022-usb.rules /etc/udev/rules.d/

deb:
	fakeroot checkinstall --default --requires python3-libusb1 --install=no --backup=no --deldoc=yes

clean:
	-rm *~ .*~ 
	( cd $(BE) && make clean )
	( cd $(BL) && make clean )

