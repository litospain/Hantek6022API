all: fx2upload

CXXFLAGS = -Wall -Wextra $(shell pkg-config --cflags libusb-1.0)
LDLIBS = $(shell pkg-config --libs libusb-1.0)

fx2upload: fx2upload.o cypress.o

fx2upload.o: fx2upload.cpp cypress.h

cypress.o: cypress.cpp


clean:
	-rm fx2upload *.o *~
