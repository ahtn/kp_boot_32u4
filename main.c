// Copyright 2018 jem@seethis.link
// Licensed under the MIT license (http://opensource.org/licenses/MIT)

#include <avr/boot.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>
#include <avr/wdt.h>
#include <util/delay.h>

#include "usb.h"
#include "usb_32u4.h"

#define CPU_PRESCALE(n) (CLKPR = 0x80, CLKPR = (n))

#define MAGIC_ADDRESS (0x0100)

void spm_leap_cmd(uint16_t addr, uint8_t spmCmd, uint16_t optValue);

int main(void) {
    cli();

    // set for 16 MHz clock
    CPU_PRESCALE(0);

#if 0
    // Check if we should enter the bootloader
    if (
        (pgm_read_word(0x0000) != 0xFFFF) &&
        ((uint32_t*)(MAGIC_ADDRESS) != 0x)
    ) {

    }
#endif

    wdt_reset();
    WDTCSR = (1<<WDCE) | (1<<WDE);
    WDTCSR = (1<<WDE) | (0<<WDP3) | (1<<WDP2) | (0<<WDP1) | (0<<WDP0);

#if defined(USE_KEYBOARD_TEST)
    DDRF |= _BV(7) | _BV(6);
    PORTF |= _BV(7) | _BV(6);
#endif

    usb_init();

    while (1) {
        usb_poll();

        wdt_reset();
    }
}
