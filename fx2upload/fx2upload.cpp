// SPDX-License-Identifier: GPL-2.0-or-later

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "cypress.h"


int usage() {
	puts( "usage: fx2upload [OPTIONS] FIRMWARE [VID PID]" );
	puts( "  uploads firmware to a Cypress FX2 USB device identified by VID and PID" );
	puts( "  OPTIONS:   -v verbose ");
	puts( "  FIRMWARE:  intel hex file" );
	puts( "  VID:       VendorID as hex value, default =  0x04B4" );
	puts( "  PID:       ProductID as hex value, default = 0x8613" );
	exit( 1 );
}


int errorexit( const char* errstr, int errno = -1 ) {
	fputs( errstr, stderr );
	exit( errno );
}


int main(int argc, char **argv) {

	bool verbose = ( argc > 1 && !strcmp( argv[1], "-v" ) );

	if ( verbose ) {
		--argc;
		++argv;
	}

	if ( argc != 2 && argc != 4 ) {
		usage();
	}

	FILE *firmware = fopen( argv[ 1 ], "rb" );
	if ( firmware == nullptr ) {
		errorexit( "ERROR: Unable to open firmware file\n" );
	}

	fseek( firmware, 0L, SEEK_END );
	int hexsize = ftell( firmware );
	rewind( firmware );

	char *ihex = (char*)calloc( hexsize, 1 );
	if ( ihex == nullptr )
		errorexit( "ERROR: Unable to alloc memory\n" );

	int status = fread( ihex, hexsize, 1, firmware );

	if ( status == 1 ) {
		if ( verbose )
			printf( "read %d bytes from %s\n", hexsize, argv[ 1 ] );
	} else {
		errorexit( "ERROR: Unable to read firmware file\n" );
	}

	uint16_t vid = 0x04B4;
	uint16_t pid = 0x8613;

	if ( argc == 4 ) {
		vid = uint16_t( strtoul( argv[ 2 ], NULL, 16 ) );
		pid = uint16_t( strtoul( argv[ 3 ], NULL, 16 ) );
		if ( !vid || !pid )
			usage();
	}

	Cypress cypress;
	status = cypress.claimDevice( vid, pid );
	if ( status )
		return status;
	if ( verbose )
		printf( "claimed device %04X:%04X\n", vid, pid );
	status = cypress.uploadIhxFirmware( ihex, hexsize );
	if ( status ) {
		printf( "status: %d\n", status );
		return status;
	}
	if ( verbose )
		printf( "upload ready\n" );
	return 0;
}
