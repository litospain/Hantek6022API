#define MUX_PORT IOC

/* This sets three bits for each channel, one channel at a time.
 * For channel 0 we want to set bits 5, 6 & 7
 * For channel 1 we want to set bits 2, 3 & 4
 *
 * We convert the input values that are strange due to original firmware code into the value of the three bits as follows:
 * val -> bits
 * 1  -> 010b
 * 2  -> 001b
 * 5  -> 000b
 * 10 -> 011b
 *
 * The third bit is always zero since there are only four outputs connected in the serial selector chip.
 *
 * The multiplication of the converted value by 0x24 sets the relevant bits in
 * both channels and then we mask it out to only affect the channel currently
 * requested.
 */
BOOL set_voltage(BYTE channel, BYTE val)
{
    BYTE bits, mask;
    switch (val) {
    case 1:
	bits = 0x24 * 2;
	break;
    case 2:
	bits = 0x24 * 1;
	break;
    case 5:
	bits = 0x24 * 0;
	break;
    case 10:
	bits = 0x24 * 3;
	break;
    default:
	return FALSE;
    }

    mask = channel ? 0xe0 : 0x1c;
    MUX_PORT = (MUX_PORT & ~mask) | (bits & mask);
    return TRUE;
}

