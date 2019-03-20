//
// Bit definitions that are different between 6022BE and 6022BL
//
// This is the 6022BL version
//


// Port A
// PA0 ---
// PA1 MUX0.0
// PA2 MUX0.1
// PA3 MUX0.2
// PA4 MUX1.0
// PA5 MUX1.1
// PA6 MUX1.2
// PA7 ANALOG_MODE
// Port C
// PC0 LED_RED
// PC1 LED_GREEN
// PC2 CAL_OUT
// PC3 ---
// PC4 ---
// PC5 ---
// PC6 ---
// PC7 ---


// goes into fw.c - main()
// 1: bit is output
#define INIT_OEC 0x07
#define INIT_OEA 0xFE


#define LED_RED PC0
#define LED_GREEN PC1
#define LED_ON 0
#define LED_OFF 1


// 2V @ 1kHz output
#define CAL_OUT PC2


// 6022BL special
#define SET_ANALOG_MODE() do { PA7 = 1; } while (0)


// Frontend gain setting for 6022BL
// We set three bits of port A for each channel
// For channel 0 we use bits 1, 2 & 3 (MSB) 
// For channel 1 we use bits 4, 5 & 6 (MSB)
// PA:       -111.000-
// BITS:     0001.0010  = 0x12
// MASK_CH0: 0000.1110  = 0x0E
// MASK_CH1: 0111.0000  = 0x70
// MSB is always zero.

#define MUX_PORT IOA
#define MUX_BITS 0x12
#define MASK_CH0 0x0E
#define MASK_CH1 0x70


// GPIF setting
// OEx = 1, CTLx = 0
#define OUT0 0x10
// OEx = CTLx = 1
#define OE_CTL 0x11

