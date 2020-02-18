#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "libusb.h"
#include "fx2util.h"

int main(int argc, char **argv) {
	if ( argc < 4 ) {
		printf( "usage: fx2hexload <vid> <pid> <file.ihx>\n" );
		exit( 0 );
	}


	if ( libusb_init( NULL ) <0 ) {
		printf( "libusb init error\n" );
		exit( 1 );
	}

	libusb_set_option( NULL, LIBUSB_OPTION_LOG_LEVEL, 0 );

	int vid=strtol( argv[ 1 ], NULL, 16 );
	int pid=strtol( argv[ 2 ], NULL, 16 );

	libusb_device_handle *device = 
		libusb_open_device_with_vid_pid( NULL, (uint16_t)vid, (uint16_t)pid );
	if ( device == nullptr ) {
		printf( "libusb open device error\n" );
		exit( 1 );
	}

	libusb_set_auto_detach_kernel_driver( device, 1 );
	if ( libusb_claim_interface( device, 0 ) != LIBUSB_SUCCESS ) {
		printf( "libusb claim interface error\n" );
		exit( 1 );
	}

	FILE *firmware = fopen( argv[ 3 ], "rb" );
	if ( firmware == NULL ) {
		printf( "Unable to open file\n" );
		exit( 1 );
	}

	fseek( firmware, 0L, SEEK_END );
	int hexsize = ftell( firmware );
	rewind( firmware );

	char *ihex = (char*)calloc( hexsize, 1 );

	int status = fread( ihex, hexsize, 1, firmware );

	if ( status == 1 ) {
		printf( "%d bytes read from %s\n", hexsize, argv[ 3 ] );
	}
 
	if ( CypressUploadIhxFirmware( device, ihex, hexsize ) == 1 ) {
		printf( "Firmware uploaded\n" );
	} else {
		printf( "Firmware upload failed\n" );
	}
}
