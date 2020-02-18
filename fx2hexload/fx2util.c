#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "libusb.h"
#include "fx2util.h"


static const unsigned int reset_address = 0xE600;


int parse_hex_line( const char *theline, char *bytes, int *addr, int *num, int *rectyp )
{
	int sum, len, cksum;
	const char *ptr;

	*num = 0;
	if (theline[0] != ':') return 0;
	if (strlen(theline) < 11) return 0;

	ptr = theline+1;
	if (!sscanf(ptr, "%02x", &len)) return 0;
	ptr += 2;
	if ( strlen(theline) < (11 + (len * 2)) ) return 0;
	if (!sscanf(ptr, "%04x", addr)) return 0;
	ptr += 4;
	//  printf("Line: length=%d Addr=%d\n", len, *addr); 
	if (!sscanf(ptr, "%02x", rectyp)) return 0;
	ptr += 2;
	sum = (len & 255) + ((*addr >> 8) & 255) + (*addr & 255) + (*rectyp & 255);
	while(*num != len) {
		if (!sscanf(ptr, "%02x", (int *)&bytes[*num])) return 0;
		ptr += 2;
		sum += bytes[*num] & 255;
		(*num)++;
		if (*num >= 256) return 0;
	}
	if (!sscanf(ptr, "%02x", &cksum)) return 0;
	if ( ((sum & 255) + (cksum & 255)) & 255 ) return 0; /* checksum error */
	return 1;
}


int CypressWriteRam( libusb_device_handle *device, unsigned int addr, unsigned char *buf, unsigned int len) {
	return libusb_control_transfer( device,
			LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE,
			0xA0,
			addr & 0xFFFF,
			addr >> 16,
			buf,
			len,
			1000
		);
}


int CypressReset( libusb_device_handle *device, unsigned char suspended ) {
	return CypressWriteRam( device, reset_address, &suspended, 1 );
}


int CypressUploadIhxFirmware( libusb_device_handle *device, const char *buf, unsigned int len ) {

	char* tempBuf = (char*)malloc( len + 1 );
	tempBuf[len] = 0;
	memcpy( tempBuf, buf, len );

	char* line = strtok(tempBuf,"\n");	

	int i = CypressReset( device, 1 );

	if ( i < 0 ) {
		free( tempBuf );
	 	return i;
	}

	char bytes[ 256 ];
	int addr, num, rectyp;
	while ( ( line != NULL ) && ( rectyp !=1 ) ) {
		parse_hex_line( line, bytes, &addr, &num, &rectyp );

		if ( rectyp == 0 ) {
			i = CypressWriteRam( device, addr, (unsigned char*)&bytes, num );
			if ( i < 0 ) {
				free( tempBuf );
		 		return i;
			}

		}
		if ( rectyp != 1 )
			line = strtok( NULL, "\n" );
	}
	free( tempBuf );
	i = CypressReset( device, 0 );
	if ( i < 0 ) {
		 return i;
	}
	return 1;
}
