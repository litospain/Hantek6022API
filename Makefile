all: fw_custom_BE fw_custom_BL fx2upload

BE=PyHT6022/HantekFirmware/custom_BE
BL=PyHT6022/HantekFirmware/custom_BL
BEb=$(BE)/build
BLb=$(BL)/build

.PHONY: fw_custom_BL
fw_custom_BE:
	cd $(BE) && make

.PHONY: fw_custom_BL
fw_custom_BL:
	cd $(BL) && make

.PHONY: fx2upload
fx2upload:
	cd fx2upload && make


.PHONY: install
install: all
	python3 setup.py install
	if [ -d /etc/udev/rules.d/ ]; then cp 60-hantek-6022-usb.rules /etc/udev/rules.d/; fi
	install examples/*_6022*.py /usr/local/bin

.PHONY: deb
deb:
	fakeroot checkinstall --default --requires python3-libusb1 --install=no --backup=no --deldoc=yes

.PHONY: debinstall
debinstall: deb
	sudo dpkg -i `ls hantek6022api_*.deb | tail -1`


.PHONY: clean
clean:
	-rm *~ .*~ 
	( cd $(BE) && make clean )
	( cd $(BL) && make clean )
	( cd fx2upload && make clean )


.PHONY: xfer
xfer:
	cp PyHT6022/HantekFirmware/custom_BE/dso6022be-firmware.hex \
	../OpenHantek/OpenHantek6022/openhantek/res/firmware
	cp PyHT6022/HantekFirmware/custom_BL/dso6022bl-firmware.hex \
	../OpenHantek/OpenHantek6022/openhantek/res/firmware
