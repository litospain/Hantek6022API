all: fx2hexload

fx2hexload: fx2hexload.c fx2util.c fx2util.h
	g++ fx2hexload.c fx2util.c -lusb-1.0 -I/usr/include/libusb-1.0 -o $@

clean:
	rm fx2hexload *~
