import usb.core


VENDOR_INSTRUSTAR = 0xd4a2
PRODUCT_ISDS205B = 0x5661
device = usb.core.find(idVendor=VENDOR_INSTRUSTAR, idProduct=PRODUCT_ISDS205B)
device.set_configuration(1)
device.ctrl_transfer(0x40,0xA0,0xE600,0,b'\x01') #Halts cpu

fd= open('isds205b-firmware.hex', 'r')

while fd.read(1)==':':
	bytes_in_line = fd.read(2)
	bytes_len=int(bytes_in_line,16)
	addres = fd.read(4)
	int_addres=int(addres,16)
	record_type = fd.read(2) 	#debe ser 0, sino hay que mirar el intel hex format, un 2 indica que lo que viene a continuacion <<4 es la base addres de la siguiente linea
	record = int(record_type,16)
	if record is not 0:
		print('error')
	data_str = fd.read(bytes_len*2)
	data = bytes.fromhex(data_str)
	checksum=fd.read(2)
	rn=fd.read(1)
	#print('0x{:04X}: {}'.format(int_addres, data_str))
	device.ctrl_transfer(0x40,0xA0,int_addres,0,data)
fd.close()

device.ctrl_transfer(0x40,0xA0,0xE600,0,b'\x00')


#fd=open('eepromdump', 'wb')
#for i in range(128):
#	data=device.ctrl_transfer(0xC0,0xA2,i*64,0,64)
#	fd.write(data)
#fd.close()
device.finalize()

