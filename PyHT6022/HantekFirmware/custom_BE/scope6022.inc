/*
 * This file is taken from the sigrok-firmware-fx2lafw project.
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

// CLK_12M; CLK_24M; CLK_48M
#define CPU_FREQ  CLK_48M
// 12 MHz: 500; 24 MHz: 1000; 48 MHz: 2000
#define TIMER2_VAL 2000

#define OE_CTL (((1 << CTL_BIT) << 4) | (1 << CTL_BIT)) /* OEx = CTLx = 1 */

static BOOL set_voltage(BYTE channel, BYTE val);

struct samplerate_info {
	BYTE rate;
	BYTE wait0;
	BYTE wait1;
	BYTE opc0;
	BYTE opc1;
	BYTE out0;
	BYTE ifcfg;
};


/* Change to support as many interfaces as you need. */
static BYTE altiface = 0;
static BYTE samplerate = 0;
static BYTE numchannels = 2;
static BYTE fifocfg = 0;

static volatile WORD ledinit = 500;
static volatile WORD ledcounter = 500;

static volatile __bit dosud = FALSE;
static volatile __bit dosuspend = FALSE;

extern __code BYTE highspd_dscr;
extern __code BYTE fullspd_dscr;


void resume_isr(void) __interrupt RESUME_ISR
{
	CLEAR_RESUME();
}


void sudav_isr(void) __interrupt SUDAV_ISR
{
	dosud = TRUE;
	CLEAR_SUDAV();
}


void usbreset_isr(void) __interrupt USBRESET_ISR
{
	handle_hispeed(FALSE);
	CLEAR_USBRESET();
}


void hispeed_isr(void) __interrupt HISPEED_ISR
{
	handle_hispeed(TRUE);
	CLEAR_HISPEED();
}


void suspend_isr(void) __interrupt SUSPEND_ISR
{
	dosuspend = TRUE;
	CLEAR_SUSPEND();
}


void timer2_isr(void) __interrupt TF2_ISR
{
	/* Toggle the probe calibration pin, only accurate up to ca. 8MHz. */
	TOGGLE_CALIBRATION_PIN();
	if ( ledcounter-- == 0 ) {	// led timed out
		ledcounter = ledinit;	// reload
		LED_RED_TOGGLE();
	}
	TF2 = 0;
}


#if 0
/**
 * Each LSB in the nibble of the byte controls the coupling per channel.
 *
 * Setting PE3 disables AC coupling capacitor on CH0.
 * Setting PE0 disables AC coupling capacitor on CH1.
 */
static void set_coupling(BYTE coupling_cfg)
{
	if (coupling_cfg & 0x01)
		IOE |= 0x08;
	else
		IOE &= ~0x08;

	if (coupling_cfg & 0x10)
		IOE |= 0x01;
	else
		IOE &= ~0x01;
}
#endif


void set_aadj() {
	if (samplerate >= 24000 / numchannels) {
		EP2ISOINPKTS &= 0x7f;
	} else {
		EP2ISOINPKTS |= 0x80;
	}
}


static BOOL set_numchannels(BYTE num)
{
	numchannels = num;
	if (numchannels == 1 || numchannels == 2) {
		fifocfg = 7 + numchannels;
		EP2FIFOCFG = fifocfg;
		EP6FIFOCFG = fifocfg;
		set_aadj();
		return TRUE;
	}
	return FALSE;
}


static void clear_fifo(void)
{
	GPIFABORT = 0xff;
	SYNCDELAY3;
	while (!(GPIFTRIG && 0x80))
		;
	FIFORESET = 0x80;
	SYNCDELAY3;
	EP2FIFOCFG = 0;
	SYNCDELAY3;
	EP6FIFOCFG = 0;
	SYNCDELAY3;
	FIFORESET = 0x02;
	SYNCDELAY3;
	FIFORESET = 0x06;
	SYNCDELAY3;
	EP2FIFOCFG = fifocfg;
	SYNCDELAY3;
	EP6FIFOCFG = fifocfg;
	SYNCDELAY3;
	FIFORESET = 0;
}


static void stop_sampling(void)
{
	GPIFABORT = 0xff;
	SYNCDELAY3;
	INPKTEND = (altiface == 0) ? 6 : 2;
}


static void start_sampling(void)
{
	int i;

	SET_ANALOG_MODE();

	clear_fifo();

	for (i = 0; i < 1000; i++)
		;

	while (!(GPIFTRIG & 0x80))
		;

	SYNCDELAY3;
	GPIFTCB1 = 0x28;
	SYNCDELAY3;
	GPIFTCB0 = 0;
	GPIFTRIG = (altiface == 0) ? 6 : 4;
}


static void select_interface(BYTE alt)
{
	const BYTE *pPacketSize = \
		((USBCS & bmHSM) ? &highspd_dscr : &fullspd_dscr)
		+ ( 9 + 9 + 4 + alt * ( 9 + 7 ) );

	altiface = alt;

	if (alt == 0) {
		/* Bulk on EP6. */
		EP2CFG = 0x00;
		EP6CFG = 0xe0;
		EP6GPIFFLGSEL = 1;
		EP6AUTOINLENL = pPacketSize[0];
		EP6AUTOINLENH = pPacketSize[1];
	} else {
		/* Iso on EP2. */
		EP2CFG = 0xd8;
		EP6CFG = 0x00;
		EP2GPIFFLGSEL = 1;
		EP2AUTOINLENL = pPacketSize[0];
		EP2AUTOINLENH = pPacketSize[1] & 0x7;
		EP2ISOINPKTS = (pPacketSize[1] >> 3) + 1;
		set_aadj();
	}
}


// struct samplerate_info{ rate, wait0, wait1, opc0, opc1, out0, ifcfg };
// rate -> ID 
// wait0, wait1, opc0, opc1, out0 -> GPIF waveform registers
// ifcfg -> IFCONFIG register (TRM 15.5.2)
//
// IFCONFIG.7 : IFCLKSRC, 0: ext, 1: int (30/48 MHz)
// IFCONFIG.6 : 3048MHZ, 0: 30MHz, 1: 48MHz
// IFCONFIG.5 : IFCLKOE, 0: tri-state, 1: drive
// IFCONFIG.4 : IFCLKPOL, 0: normal polarity, 1: inverted
// IFCONFIG.3 : ASYNC, 0: synchronously, clock supplied to IFCLK pin, 1: asynchronously, FIFO provides r/w strobes
// IFCONFIG.2 : GSTATE, 1: PE.[10] = GSTATE.[10]
// IFCONFIG.[10] : 00: ports, 01: reserved, 10: GPIF (internal) master, 11: slave FIFO (external master)
//

#define IFCLK48 0xca
#define IFCLK30 0x8a

#if 1
static const struct samplerate_info samplerates[] = {
	{  48, 0x80,   0, 3, 0, 0x00, 0xea },
	{  30, 0x80,   0, 3, 0, 0x00, 0xaa },
	{  24,    1,   0, 2, 1, OUT0, IFCLK48 },
	{  15,    1,   0, 2, 1, OUT0, IFCLK30 },
	{  12,    2,   1, 2, 0, OUT0, IFCLK48 },
	{  10,    1,   1, 2, 0, OUT0, IFCLK30 },
	{   5,    3,   2, 2, 0, OUT0, IFCLK30 },
	{   2,    7,   7, 2, 0, OUT0, IFCLK30 },
	{   1,   15,  14, 2, 0, OUT0, IFCLK30 },
	{ 150,   30,  29, 2, 0, OUT0, IFCLK30 },
	{ 120,   75,  74, 2, 0, OUT0, IFCLK30 },
	{ 110,  150, 149, 2, 0, OUT0, IFCLK30 },
	{ 106,  250, 249, 2, 0, OUT0, IFCLK30 }
};
#else
static const struct samplerate_info samplerates[] = {
	{  48, 0x80,   0, 3, 0, 0x00, 0xea },
	{  30, 0x80,   0, 3, 0, 0x00, 0xaa },
	{  24,    1,   0, 2, 1, OUT0, 0xca },
	{  16,    1,   1, 2, 0, OUT0, 0xca },
	{  12,    2,   1, 2, 0, OUT0, 0xca },
	{   8,    3,   2, 2, 0, OUT0, 0xca },
	{   4,    6,   5, 2, 0, OUT0, 0xca },
	{   2,   12,  11, 2, 0, OUT0, 0xca },
	{   1,   24,  23, 2, 0, OUT0, 0xca },
	{  50,   48,  47, 2, 0, OUT0, 0xca },
	{  20,  120, 119, 2, 0, OUT0, 0xca },
	{  10,  240, 239, 2, 0, OUT0, 0xca }
};
#endif


static BOOL set_samplerate(BYTE rate)
{
	BYTE i = 0;

	while (samplerates[i].rate != rate) {
		i++;
		if ( i == sizeof(samplerates) / sizeof(samplerates[0]) )
			return FALSE;
	}

	IFCONFIG = samplerates[i].ifcfg;

	AUTOPTRSETUP = 7;
	AUTOPTRH2 = 0xE4; /* 0xE400: GPIF waveform descriptor 0. */
	AUTOPTRL2 = 0x00;

	/*
	 * The program for low-speed, e.g. 1 MHz, is:
	 * wait 24, CTLx=0, FIFO
	 * wait 23, CTLx=1
	 * jump 0, CTLx=1
	 *
	 * The program for 24 MHz is:
	 * wait 1, CTLx=0, FIFO
	 * jump 0, CTLx=1
	 *
	 * The program for 30/48 MHz is:
	 * jump 0, CTLx=Z, FIFO, LOOP
	 *
	 * (CTLx is device-dependent, could be e.g. CTL0 or CTL2.)
	 */

	/* LENGTH / BRANCH 0-7 */
	EXTAUTODAT2 = samplerates[i].wait0;
	EXTAUTODAT2 = samplerates[i].wait1;
	EXTAUTODAT2 = 1;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;

	/* OPCODE 0-7 */
	EXTAUTODAT2 = samplerates[i].opc0;
	EXTAUTODAT2 = samplerates[i].opc1;
	EXTAUTODAT2 = 1; /* DATA=0 DP=1 */
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;

	/* OUTPUT 0-7 */
	EXTAUTODAT2 = samplerates[i].out0;
	EXTAUTODAT2 = OE_CTL;
	EXTAUTODAT2 = OE_CTL;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;

	/* LOGIC FUNCTION 0-7 */
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;
	EXTAUTODAT2 = 0;

	for (i = 0; i < 96; i++)
		EXTAUTODAT2 = 0;

	return TRUE;
}


static BOOL set_calibration_pulse( BYTE freq )
{
	switch ( freq ) {
	case 105:		// 50 Hz
		ledinit = 25;
		RCAP2L = -40000L & 0xff;
		RCAP2H = (-40000L & 0xff00) >> 8;
		break;
	case 0:
	case 110:		// 100 Hz
		ledinit = 50;
		RCAP2L = -20000 & 0xff;
		RCAP2H = (-20000 & 0xff00) >> 8;
		break;
	case 120:		// 200 Hz
		ledinit = 100;
		RCAP2L = -10000 & 0xff;
		RCAP2H = (-10000 & 0xff00) >> 8;
		break;
	case 150:		// 500 Hz
		ledinit = 250;
		RCAP2L = -4000 & 0xff;
		RCAP2H = (-4000 & 0xff00) >> 8;
		break;
	case 1:			// 1kHz
		ledinit = 500;
		RCAP2L = -2000 & 0xff;
		RCAP2H = (-2000 & 0xff00) >> 8;
		break;
	case 2:			// 2kHz
		ledinit = 1000;
		RCAP2L = -1000 & 0xff;
		RCAP2H = (-1000 & 0xff00) >> 8;
		break;
	case 5:			// 5kHz
		ledinit = 2500;
		RCAP2L = -400 & 0xff;
		RCAP2H = (-400 & 0xff00) >> 8;
		break;
	case 10:		// 10kHz
		ledinit = 5000;
		RCAP2L = (BYTE)(-200 & 0xff);
		RCAP2H = (-200 & 0xff00) >> 8;
		break;
	case 20:		// 20kHz
		ledinit = 10000;
		RCAP2L = (BYTE)(-100 & 0xff);
		RCAP2H = (-100 & 0xff00) >> 8;
		break;
	case 50:		// 50kHz
		ledinit = 25000;
		RCAP2L = (BYTE)(-40 & 0xff);
		RCAP2H = (-40 & 0xff00) >> 8;
		break;
	case 100:		// 100kHz
		ledinit = 50000;
		RCAP2L = (BYTE)(-20 & 0xff);
		RCAP2H = (-20 & 0xff00) >> 8;
		break;
	default:
		return FALSE;
	}
	return TRUE;
}


/* Set *alt_ifc to the current alt interface for ifc. */
BOOL handle_get_interface(BYTE ifc, BYTE *alt_ifc)
{
	(void)ifc;
	*alt_ifc = altiface;
	return TRUE;
}


/*
 * Return TRUE if you set the interface requested.
 *
 * Note: This function should reconfigure and reset the endpoints
 * according to the interface descriptors you provided.
 */
BOOL handle_set_interface(BYTE ifc,BYTE alt_ifc)
{
	if (ifc == 0)
		select_interface(alt_ifc);

	return TRUE;
}


BYTE handle_get_configuration(void)
{
	/* We only support configuration 0. */
	return 0;
}


BOOL handle_set_configuration(BYTE cfg)
{
	/* We only support configuration 0. */
	(void)cfg;
	return TRUE;
}


// handle reading and writing EEPROM data
BOOL eeprom() {
	WORD addr=SETUP_VALUE(), len=SETUP_LENGTH();
	// wait for ep0 not busy
	while ( EP0CS & bmEPBUSY )
		;
	switch ( SETUP_TYPE ) {
		case 0xc0: // read access
			while ( len ) { // still have bytes to read
				BYTE cur_read = len > 64 ? 64 : len; // can't read more than 64 bytes at a time
				while ( EP0CS&bmEPBUSY ) // can't do this until EP0 is ready
					;
				eeprom_read( 0x51, addr, cur_read, EP0BUF );
				EP0BCH=0;
				SYNCDELAY3;
				EP0BCL=cur_read;
				len -= cur_read;
				addr += cur_read;
			}
			break;
		case 0x40: // write access
			while ( len ) {
				BYTE cur_write;
				// printf ( "Len More Bytes %d\n" , len );
				EP0BCL = 0; // allow pc transfer in
				while ( EP0CS & bmEPBUSY ) // wait
					;
				cur_write = EP0BCL;
				// printf ( "Writing %d Bytes to %d..\n", cur_write, addr );
				if ( !eeprom_write( 0x51, addr, cur_write, EP0BUF ) )
					return FALSE;
				addr += cur_write;
				len -= cur_write;
			}
			break;
		default:
			return FALSE; // bad type
	}
	return TRUE;
}


BOOL handle_get_descriptor() {
	return FALSE;
}


BOOL handle_vendorcommand(BYTE cmd)
{
	stop_sampling();

	/* Set red LED, toggle after timeout. */
	LED_RED();
	ledcounter = 1000;

	/* Clear EP0BCH/L for each valid command. */
	if ( cmd >= 0xe0 && cmd <= 0xe6 ) {
		EP0BCH = 0;
		EP0BCL = 0;
		while ( EP0CS & bmEPBUSY )
			;
	}

	switch (cmd) {
		case 0xa2:
			return eeprom();

		case 0xe0:
			return set_voltage( 0, EP0BUF[0] );

		case 0xe1:
			return set_voltage( 1, EP0BUF[0] );

		case 0xe2:
			return set_samplerate( EP0BUF[0] );

		case 0xe3:
			if ( EP0BUF[0] == 1 ) {
				/* Set green LED, toggle red LED afterwards. */
				LED_GREEN();
				ledcounter = ledinit;
				start_sampling();
			}
			return TRUE;

		case 0xe4:
			return set_numchannels( EP0BUF[0] );

		case 0xe5:
			SET_COUPLING( EP0BUF[0] );
			return TRUE;

		case 0xe6:
			return set_calibration_pulse( EP0BUF[0] );

	}

	return FALSE; /* Not handled by handlers. */
}


static void init(void)
{
	EP4CFG = 0;
	EP8CFG = 0;

	SET_ANALOG_MODE();

	/* In idle mode tristate all outputs. */
	GPIFIDLECTL = 0x00; /* Don't enable CTL0-5 outputs. */
	GPIFCTLCFG = 0x80; /* TRICTL=1. CTL0-2: CMOS outputs, tri-statable. */
	GPIFWFSELECT = 0x00;
	GPIFREADYSTAT = 0x00;

	stop_sampling();

	set_voltage(0, 1);
	set_voltage(1, 1);
	set_samplerate(1);
	set_numchannels(2);
	select_interface(0);
}


static void main(void)
{
	/* Save energy. */
	SETCPUFREQ( CPU_FREQ );

	init();

	/* Set up interrupts. */
	USE_USB_INTS();

	ENABLE_SUDAV();
	ENABLE_USBRESET();
	ENABLE_HISPEED(); 
	ENABLE_SUSPEND();
	ENABLE_RESUME();

	/* Global (8051) interrupt enable. */
	EA = 1;

	/* Init timer2. */
	RCAP2L = -TIMER2_VAL & 0xff;
	RCAP2H = (-TIMER2_VAL & 0xff00) >> 8;
	T2CON = 0;
	ET2 = 1;
	TR2 = 1;

	RENUMERATE_UNCOND();
	// RENUMERATE();
	// USBCS &= ~bmDISCON;

	// PORTECFG = 0;
	PORTCCFG = 0;
	PORTACFG = 0;
	// OEE = 0xff;
	OEC = 0xff;
	OEA = 0xff; 
	LED_RED();

	while (TRUE) {
		if (dosud) {
			dosud = FALSE;
			handle_setupdata();
		}

		if (dosuspend) {
			dosuspend = FALSE;
			do {
				/* Make sure ext wakeups are cleared. */
				WAKEUPCS |= bmWU | bmWU2;
				SUSPEND = 1;
				PCON |= 1;
				__asm
				nop
				nop
				nop
				nop
				nop
				nop
				nop
				__endasm;
			} while (!remote_wakeup_allowed && REMOTE_WAKEUP());

			/* Resume (TRM 6.4). */
			if (REMOTE_WAKEUP()) {
				delay(5);
				USBCS |= bmSIGRESUME;
				delay(15);
				USBCS &= ~bmSIGRESUME;
			}
		}
	}
}
