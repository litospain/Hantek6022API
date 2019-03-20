//
// Bit definitions that are different between 6022BE and 6022BL
//
// This is the 6022BE version
//
 
// Port A
// PA0 ---
// PA1 ---
// PA2 ---
// PA3 ---
// PA4 ---
// PA5 ---
// PA6 ---
// PA7 CAL_OUT
// Port C
// PC0 LED_RED
// PC1 LED_GREEN
// PC2 MUX0.0
// PC3 MUX0.1
// PC4 MUX0.2
// PC5 MUX1.0
// PC6 MUX1.1
// PC7 MUX1.2


// goes into fw.c - main()
// 1: bit is output
#define INIT_OEC 0xFF
#define INIT_OEA 0x80


#define LED_RED PC0
#define LED_GREEN PC1
#define LED_ON 0
#define LED_OFF 1


// 2V @ 1kHz output
#define CAL_OUT PA7


// not needed/used
#define SET_ANALOG_MODE()


// Frontend gain setting for 6022BE
// 
// We set three bits of port C for each channel
// For channel 0 we use bits 2, 3 & 4 (MSB)
// For channel 1 we use bits 5, 6 & 7 (MSB)
// PC:       1110.00--
// BITS:     0010.0100  = 0x24
// MASK_CH0: 0001.1100  = 0x1C
// MASK_CH1: 1110.0000  = 0xE0
// MSB is always zero.
//
#define MUX_PORT IOC
#define MUX_BITS 0x24
#define MASK_CH0 0x1C
#define MASK_CH1 0xE0


// GPIF setting
// OEx = 1, CTLx = 0
#define OUT0 0x40
// OEx = CTLx = 1
#define OE_CTL 0x44

