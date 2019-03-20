all: fw_custom_BE fw_custom_BL

BE=PyHT6022/HantekFirmware/custom_BE
BL=PyHT6022/HantekFirmware/custom_BL
BEb=$(BE)/build
BLb=$(BL)/build

fw_custom_BE:
	cd $(BE) && make

fw_custom_BL:
	cd $(BL) && make

install:
	python3 setup.py install
	cp 60-hantek-6022-usb.rules /etc/udev/rules.d/

deb:
	fakeroot checkinstall --default --requires python3-libusb1 --install=no --backup=no --deldoc=yes

clean:
	-rm *~ .*~ 
	-rm $(BE)/*~
	-rm $(BL)/*~
	-rm $(BEb)/*.asm $(BEb)/*.a51 $(BEb)/*.rel $(BEb)/*.sym $(BEb)/*.lst $(BEb)/*.rst 
	-rm $(BEb)/*.lk $(BEb)/*.map $(BEb)/*.mem
	-rm $(BLb)/*.asm $(BLb)/*.a51 $(BLb)/*.rel $(BLb)/*.sym $(BLb)/*.lst $(BLb)/*.rst
	-rm $(BLb)/*.lk $(BLb)/*.map $(BLb)/*.mem

