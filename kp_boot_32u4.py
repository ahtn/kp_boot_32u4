#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import easyhid

from hexdump import hexdump

USB_VID = 0x6666
USB_PID = 0x9999

def find_devices(vid=USB_VID, pid=USB_PID):
    hid_devices = easyhid.Enumeration().find(vid=vid, pid=pid)
    return [BootloaderDevice(dev) for dev in hid_devices]

class BootloaderDevice(object):
    def __init__(self, hid_dev):
        self.hid_dev = hid_dev

    def open(self):
        self.hid_dev.open()

    def close(self):
        self.hid_dev.close()

    def write(self, data):
        print("Writing to device -> ")
        hexdump(bytes(data))
        self.hid_dev.write(data)

    def read(self):
        print("Read from device -> ")
        data = self.hid_dev.read()
        hexdump(bytes(data))
        return data

if __name__ == "__main__":
    dev = find_devices()[0]

    dev.open()
    dev.write(list(range(0,32)))
    dev.read()
