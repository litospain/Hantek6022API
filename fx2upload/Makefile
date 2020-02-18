all: fx2upload

CXXFLAGS = -Wall
LDFLAGS = -lusb-1.0

fx2upload: fx2upload.o cypress.o

fx2upload.o: fx2upload.cpp cypress.h

cypress.o: cypress.cpp


clean:
	-rm fx2upload *.o *~
