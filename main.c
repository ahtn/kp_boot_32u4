// Copyright 2018 jem@seethis.link
// Licensed under the MIT license (http://opensource.org/licenses/MIT)

#include <avr/boot.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>
#include <util/delay.h>

#include "usb.h"
#include "usb_32u4.h"

#define CPU_PRESCALE(n) (CLKPR = 0x80, CLKPR = (n))

void spm_leap_cmd(uint16_t addr, uint8_t spmCmd, uint16_t optValue);

int main(void) {
    // set for 16 MHz clock
    CPU_PRESCALE(0);

#if defined(USE_KEYBOARD_TEST)
    DDRF |= _BV(7) | _BV(6);
    PORTF |= _BV(7) | _BV(6);
#endif

    cli();

    usb_init();

    while (1) {
        usb_poll();
    }
}
