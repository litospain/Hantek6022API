// SPDX-License-Identifier: GPL-2.0-or-later

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "cypress.h"


int Cypress::claimDevice( uint16_t vid, uint16_t pid ) {
	if ( libusb_init( NULL ) < 0 ) {
		fputs( "ERROR: libusb init\n", stderr );
		return -1;
	}

	libusb_set_option( NULL, LIBUSB_OPTION_LOG_LEVEL, 0 );

	device = libusb_open_device_with_vid_pid( NULL, vid, pid );
	if ( device == nullptr ) {
		fprintf( stderr, "ERROR: libusb_open_device_with_vid_pid( %04X, %04X )\n", vid, pid );
		return -1;
	}

	libusb_set_auto_detach_kernel_driver( device, 1 );
	if ( libusb_claim_interface( device, 0 ) != LIBUSB_SUCCESS ) {
		fprintf( stderr, "ERROR: libusb claim interface\n" );
		return -1;
	}
	return 0; // success
}


int Cypress::uploadIhxFirmware( const char *buf, unsigned int len ) {
	char* tempBuf = (char*)malloc( len + 1 );
	if ( tempBuf == nullptr )
		return -1;
	tempBuf[ len ] = 0;
	memcpy( tempBuf, buf, len );

	char* line = strtok( tempBuf, "\n" );

	int status = resetFX2( 1 );

	if ( status < 0 ) {
		free( tempBuf );
		return status;
	}
	int lineNum = 0;
	char bytes[ 256 ];
	const int DataRecord = 0;
	const int EndOfRecord = 1;
	unsigned addr, num, rectyp = DataRecord;
	while ( ( line != nullptr ) && ( rectyp != EndOfRecord ) ) {
		++lineNum;
		if ( parseHexLine( line, bytes, &addr, &num, &rectyp ) )
			fprintf( stderr, "%s in line %d: %s\n", hexErr, lineNum, line );
		if ( rectyp == DataRecord ) {
			status = writeRam( addr, (unsigned char*)&bytes, num );
			if ( status < 0 ) {
				free( tempBuf );
				return status;
			}
		}
		if ( rectyp != EndOfRecord )
			line = strtok( nullptr, "\n" );
	}
	free( tempBuf );
	status = resetFX2( 0 );
	if ( status < 0 )
		return status;
	return 0; // success
}


int Cypress::parseHexLine( const char *theline, char *bytes, unsigned *addr, unsigned *num, unsigned *rectyp )
{
	unsigned sum, len, cksum;
	const char *ptr;

	*num = 0;
	if (theline[0] != ':') { hexErr = (char*)"missing :"; return -1; }
	if (strlen(theline) < 11) { hexErr = (char*)"short line"; return -1; }

	ptr = theline + 1;
	if (!sscanf(ptr, "%02x", &len)) { hexErr = (char*)"bad len"; return -1; }
	ptr += 2;
	if ( strlen(theline) < (11 + (len * 2)) ) { hexErr = (char*)""; return -1; }
	if (!sscanf(ptr, "%04x", addr)) { hexErr = (char*)"bad addr"; return -1; }
	ptr += 4;
	// printf("Line: length=%2d Addr=0x%04X\n", len, *addr);
	if (!sscanf(ptr, "%02x", rectyp)) { hexErr = (char*)"bad rectyp"; return -1; }
	ptr += 2;
	sum = (len & 255) + ((*addr >> 8) & 255) + (*addr & 255) + (*rectyp & 255);
	while(*num != len) {
		if (!sscanf(ptr, "%02x", (int*)&bytes[*num])) { hexErr = (char*)"bad data"; return -1; }
		ptr += 2;
		sum += bytes[*num] & 255;
		(*num)++;
		if ( *num >= 256 ) { hexErr = (char*)"num >= 256"; return -1; }
	}
	if (!sscanf(ptr, "%02x", &cksum)) { hexErr = (char*)"bad cksum"; return -1; }
	if ( ((sum & 255) + (cksum & 255)) & 255 ) { hexErr = (char*)"wrong cksum"; return -1; } // checksum error
	return 0; // success
}


int Cypress::writeRam( unsigned int addr, unsigned char *buf, unsigned int len) {
	return libusb_control_transfer( device,
		LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE,
		0xA0,
		addr & 0xFFFF,
		addr >> 16,
		buf,
		uint16_t( len ),
		1000
	);
}


int Cypress::resetFX2( unsigned char suspended ) {
	return writeRam( 0xE600, &suspended, 1 );
}

