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

int main(void)
{
    // set for 16 MHz clock
    CPU_PRESCALE(0);

    DDRF |= _BV(7) | _BV(6);
    PORTF |= _BV(7) | _BV(6);

    usb_init();
    sei();

#define COUNTER_LIMIT 1000000UL
    volatile uint32_t counter = 0;

    while (1) {
        usb_poll();

        counter++;
        if (counter > COUNTER_LIMIT) {
            usb_keyboard_press(KEY_B, KEY_SHIFT);
            counter = 0;
        }
    }
}
