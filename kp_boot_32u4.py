#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import easyhid
import struct

from hexdump import hexdump

USB_VID = 0x6666
USB_PID = 0x9999

EP_SIZE_VENDOR = 64

PAGE_SIZE = 128
EEPROM_LENGTH = 1024

SPMEN_bm = (1<<0)
PGERS_bm = (1<<1)
PGWRT_bm = (1<<2)
BLBSET_bm = (1<<3)
RWWSRE_bm = (1<<4)
SIGRD_bm = (1<<5)
RWWSB_bm = (1<<6)
SPMIE_bm = (1<<7)

SPM_HEADER_SIZE = 6
SPM_PAYLOAD_SIZE = EP_SIZE_VENDOR - SPM_HEADER_SIZE

USB_CMD_VERSION = 0
USB_CMD_INFO = 1
USB_CMD_ERASE = 2
USB_CMD_SPM = 3
USB_CMD_WRITE_EEPROM = 4
USB_CMD_RESET = 5

def find_devices(vid=USB_VID, pid=USB_PID):
    hid_devices = easyhid.Enumeration().find(vid=vid, pid=pid)
    return [BootloaderDevice(dev) for dev in hid_devices]

class BootloaderDevice(object):
    def __init__(self, hid_dev):
        self.hid_dev = hid_dev
        self.page_size = PAGE_SIZE
        self._mcu_has_been_reset = False
        self.eeprom_length = EEPROM_LENGTH

    def open(self):
        self.hid_dev.open()

    def close(self):
        if self._mcu_has_been_reset:
            return
        self.hid_dev.close()

    def write(self, data):
        data = bytearray(data)
        assert(len(data) <= EP_SIZE_VENDOR)
        # pad the packet to match EP_SIZE_VENDOR, required for raw HID
        data += bytearray( [0xff] * (EP_SIZE_VENDOR - len(data)) )

        print("Writing to device -> ")
        hexdump(bytes(data))
        self.hid_dev.write(data)

    def read(self):
        print("Read from device -> ")
        data = self.hid_dev.read()
        hexdump(bytes(data))
        return data

    def _spm_packet(self, cmd, address, action, data=None, length=0,
                    action2=0):
        # check that the write address is word aligned
        assert(address % 2 == 0)

        # # convert from byte to word address
        # address = address // 2

        # pad the data to fill the hole packet
        if data == None:
            data = []
        assert(len(data) <= SPM_PAYLOAD_SIZE)

        # The spm command will be repeated with the data from this section.
        # The bootloader will start at addr=6 (start of data section)

        cmd_read_end_address = length or len(data)
        cmd_read_end_address += 6

        # data += [0xff] * (SPM_PAYLOAD_SIZE - len(data))

        packet = bytearray()
        packet += struct.pack(
            "< B H B B B",
            cmd, address, action, action2, cmd_read_end_address
        )
        packet += bytearray(data)

        return packet

    def _lock_packet(self, lock_bits):
        return self._spm_packet(
            USB_CMD_SPM,
            0x0000,
            SPMEN_bm | BLBSET_bm,
            [lock_bits],
            length = 1
        )

    def _flash_erase_packet(self, address):
        return self._spm_packet(
            USB_CMD_SPM,
            address,
            SPMEN_bm | PGERS_bm,
            length = 1,
            action2 = SPMEN_bm | RWWSRE_bm,
        )

    def _flash_write_packet(self, address):
        return self._spm_packet(
            USB_CMD_SPM,
            address,
            SPMEN_bm | PGWRT_bm,
            length = 1,
            action2 = SPMEN_bm | RWWSRE_bm,
        )

    def _temporary_buffer_packet(self, address, data):
        return self._spm_packet(
            USB_CMD_SPM,
            address,
            SPMEN_bm,
            data
        )

    def _make_chunks(self, data, size):
        result = []
        pos = 0
        while pos < len(data):
            remaining_data = len(data) - pos
            if size <= remaining_data:
                new_chunk = data[pos:pos+size]
            else:
                # remaining data fits in one chunk
                new_chunk = data[pos:]
            result.append(new_chunk)
            pos += len(new_chunk)
        return result

    def write_page(self, address, data):
        assert(len(data) <= PAGE_SIZE)

        self.write(self._flash_erase_packet(address))
        self.read()

        chunks = self._make_chunks(data, SPM_PAYLOAD_SIZE)
        for (i, chunk) in enumerate(chunks):
            self.write(self._temporary_buffer_packet(
                address + i*SPM_PAYLOAD_SIZE,
                chunk
            ))
            self.read()

        self.write(self._flash_write_packet(address))
        self.read()

    def write_eeprom(self, start_address, data):
        assert(start_address + len(data) < self.eeprom_length)

        chunks = self._make_chunks(data, SPM_PAYLOAD_SIZE)
        for (i, chunk) in enumerate(chunks):
            self.write(self._spm_packet(
                USB_CMD_WRITE_EEPROM,
                start_address + i*SPM_PAYLOAD_SIZE,
                action = 0,
                data = chunk
            ))
            self.read()

    def reset_mcu(self):
        self.write([USB_CMD_RESET])
        self._mcu_has_been_reset = True


if __name__ == "__main__":


    dev = find_devices()[0]

    dev.open()
    for i in range(32):
        dev.write_page(0x4000 + i*128, [i]*128)
    # for i in range(10):
    #     dev.write_page(0x1000 + i*128, list(range(128)))
    # for i in range(10):
    #     dev.write_page(0x1000 + i*128, [0xff]*128)

    dev.write_eeprom(0x0100, list(range(128)))
    dev.write_eeprom(0x0180, [0xAA]*64)
    dev.write_eeprom(0x01C0, [0xBB]*64)
    dev.write_eeprom(0x0200, [0xCC]*64)
    dev.write_eeprom(0x0240, [0xDD]*64)
    dev.write_eeprom(0x0280, [0xEE]*64)
    dev.write_eeprom(0x02C0, [0xFF]*64)

    dev.reset_mcu()
    dev.close()
