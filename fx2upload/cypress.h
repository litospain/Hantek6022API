// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once
#include <libusb-1.0/libusb.h>

class Cypress {
public:
	int claimDevice( uint16_t vid, uint16_t pid );
	int uploadIhxFirmware( const char *buf, unsigned int len );
private:
	libusb_device_handle *device = nullptr;
	char *hexErr = (char*)"";
	int parseHexLine( const char *theline, char *bytes, unsigned *addr, unsigned *num, unsigned *rectyp );
	int writeRam( unsigned int addr, unsigned char *buf, unsigned int len);
	int resetFX2( unsigned char suspended );
};
