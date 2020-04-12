/*
 * This file is part of the sigrok-firmware-fx2lafw project.
 *
 * Copyright (C) 2009 Ubixum, Inc.
 * Copyright (C) 2015 Jochen Hoenicke
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, see <http://www.gnu.org/licenses/>.
 */

#include <fx2macros.h>
#include <fx2ints.h>
#include <autovector.h>
#include <delay.h>
#include <setupdat.h>
#include <i2c.h>
#include <eputils.h>


/* A and C and E set to PORT */
#define INIT_PORTACFG 0
#define INIT_PORTCCFG 0
#define INIT_PORTECFG 0

/* Set port E that a 6022 with AC/DC HW mod will start in DC mode like the original */
#define INIT_IOA 0x00
#define INIT_IOC 0x00
#define INIT_IOE 0x09

/* set PORT A, C, E as output */
#define INIT_OEA 0xFF
#define INIT_OEC 0xFF
#define INIT_OEE 0xFF


#define SET_ANALOG_MODE()		do { PA7 = 1; } while (0)

#define SET_COUPLING(x)			set_coupling_isds205(x)

#define TOGGLE_CALIBRATION_PIN()	do { PA7 = !PA7; } while (0)

#define LED_CLEAR()			NOP
#define LED_GREEN()			NOP
#define LED_RED()			NOP
#define LED_RED_TOGGLE()		NOP

#define SRCLK PA6
#define SRIN PA4
#define STOCLK PA5

volatile BYTE vol_state = 0 ; /* ISDS205C uses 74HC595 to expand ports, here we save his actual state. */

static void drive_74hc595(BYTE bits)
{
	BYTE i;

	for(i=0; i<8; i++)
	{
		SRCLK = 0;
		SRIN = bits>>7;
		SRCLK = 1;
		bits=bits<<1;
	}
	STOCLK = 1;
	STOCLK = 0;
}

/* CTLx pin index (IFCLK, ADC clock input). */
// #define CTL_BIT 2

/*
 * This sets three bits for each channel, one channel at a time.
 * For channel 0 we want to set bits 0, 1 & 6
 * For channel 1 we want to set bits 2, 3 & 4
 *
 * we set directly the relevant bits in
 * both channels and then we mask it out to only affect the channel currently
 * requested.
 */
static BOOL set_voltage(BYTE channel, BYTE val)
{
	BYTE bits, mask;

	switch (val) {
	case 1:
		bits = 0b00001001;
		break;
	case 2:
		bits = 0b00000110;
		break;
	case 5:
		bits = 0b00000000;
		break;
	case 10:
		bits = 0b01010110;
		break;
	case 11:
		bits = 0b01010000;
		break;
	case 12:
		bits = 0b01011111;
		break;
	default:
		return FALSE;
	}

	mask = (channel) ? 0b00011100 : 0b01000011;
	vol_state = (vol_state & ~mask) | (bits & mask);
		
	drive_74hc595(vol_state);

	return TRUE;
}

/**
 * Bits 5 & 7 of the byte controls the coupling per channel.
 *
 * Setting bit 7 enables AC coupling relay on CH0.
 * Setting bit 5 enables AC coupling relay on CH1.
 */
static void set_coupling_isds205(BYTE coupling_cfg)
{
	if (coupling_cfg & 0x01)
		vol_state &= ~0x80;
	else
		vol_state |= 0x80;

	if (coupling_cfg & 0x10)
		vol_state &= ~0x20;
	else
		vol_state |= 0x20;
		
	drive_74hc595(vol_state);
}

#include "isds205b.inc"

