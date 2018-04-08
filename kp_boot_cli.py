#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import kp_boot_32u4
import argparse

parser = argparse.ArgumentParser(
    description='Flashing script for xusb-boot bootloader'
)

parser.add_argument(
    '-f', dest='hex_file', action='store',
    type=str,
    default=None,
    help='The hexfile to flash'
),

parser.add_argument(
    '-d', dest='id', action='store',
    default=None,
    metavar="VID:PID",
    help='The VID:PID pair of the device to flash'
)

parser.add_argument(
    '-s', dest='serial',
    type=str, default=None,
    help='Serial number of the USB device to flash.'
)

parser.add_argument(
    '-l', dest='listing',action='store_const',
    const=True, default=False,
    help='If this flag is given, list the available devices'
)

parser.add_argument(
    '-e', dest='erase', action='store_const',
    const=True, default=False,
    help='Erase the flash.'
)

parser.add_argument(
    '-r', dest='reset',  action='store_const',
    const=True, default=False,
    help='Reset the mcu'
)

parser.add_argument(
    '-mcu',  action='store',
    default=None,
    help='Check that the bootloader mcu part number matches'
)

parser.add_argument(
    '-p', dest='path',  action='store',
    type=str, default=None,
    help='The device port path. This value can be used to identify a '
    ' device if it does not have a serial number. This value '
    'is not static and may change if the device is reconnected'
)

if __name__ == "__main__":
    args = parser.parse_args()

    if args.hex_file == None:
        parser.print_help()
        exit(1)

    if args.erase:
        pass

