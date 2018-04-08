#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import easyhid
import struct

from intelhex import IntelHex
from hexdump import hexdump

USB_VID = 0x6666
USB_PID = 0x9999

EP_SIZE_VENDOR = 64

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

CHIP_ID_MASK = 0x3F

CHIP_ID_TABLE = {
    0x00: ("CHIP_ID_ATmega8U2"   , 8 * 2**10   , 512),
    0x01: ("CHIP_ID_ATmega16U2"  , 16 * 2**10  , 512),
    0x02: ("CHIP_ID_ATmega32U2"  , 32 * 2**10  , 1024),

    0x03: ("CHIP_ID_ATmega16U4"  , 16 * 2**10  , 512),
    0x04: ("CHIP_ID_ATmega32U4"  , 32 * 2**10  , 1024),

    0x05: ("CHIP_ID_ATmega32U6"  , 32 * 2**10  , 1024),

    0x06: ("CHIP_ID_AT90USB646"  , 64 * 2**10  , 2048),
    0x07: ("CHIP_ID_AT90USB647"  , 64 * 2**10  , 2048),
    0x08: ("CHIP_ID_AT90USB1286" , 128 * 2**10 , 4096),
    0x09: ("CHIP_ID_AT90USB1287" , 128 * 2**10 , 4096),
}

BOOT_SIZE_MASK = 0xC000
BOOT_SIZE_bp = 6
BOOT_SIZE_00 = (0b00 << BOOT_SIZE_bp)
BOOT_SIZE_01 = (0b01 << BOOT_SIZE_bp)
BOOT_SIZE_10 = (0b10 << BOOT_SIZE_bp)
BOOT_SIZE_11 = (0b11 << BOOT_SIZE_bp)

class KpBoot32u4Error(Exception):
    pass

def find_devices(vid=USB_VID, pid=USB_PID):
    hid_devices = easyhid.Enumeration().find(vid=vid, pid=pid)
    return [BootloaderDevice(dev) for dev in hid_devices]

class BootloaderDevice(object):
    def __init__(self, hid_dev):
        self._hid_dev = hid_dev
        self._mcu_has_been_reset = False
        # self.eeprom_length = EEPROM_LENGTH
        # self.flash_length = FLASH_LENGTH

        with self._hid_dev:
            self._load_device_info()

    def open(self):
        self._hid_dev.open()

    def close(self):
        if self._mcu_has_been_reset:
            return
        self._hid_dev.close()

    def write(self, data):
        data = bytearray(data)
        assert(len(data) <= EP_SIZE_VENDOR)
        # pad the packet to match EP_SIZE_VENDOR, required for raw HID
        data += bytearray( [0xff] * (EP_SIZE_VENDOR - len(data)) )

        print("Writing to device -> ")
        hexdump(bytes(data))
        self._hid_dev.write(data)

    def read(self):
        print("Read from device -> ")
        data = self._hid_dev.read()
        hexdump(bytes(data))
        return data

    def _load_device_info(self):
        self.write([USB_CMD_INFO])
        data = self.read()

        response_cmd = data[0]
        if response_cmd != USB_CMD_INFO:
            raise KpBoot32u4Error(
                "Unexpected response for USB_CMD_INFO: {}".format(response_cmd)
            )

        self._version = data[1]

        chip_id = data[2] & CHIP_ID_MASK
        bootsz = data[2] & BOOT_SIZE_MASK

        if chip_id not in CHIP_ID_TABLE:
            raise KpBoot32u4Error("Unknown CHIP_ID: {}".format(chip_id))

        name, flash, eeprom = CHIP_ID_TABLE[chip_id]

        bootsz = bootsz >> BOOT_SIZE_bp
        mult_fact = 2**(3-bootsz)

        if flash >= 64 * 2**10:
            self._boot_size = 1024 * mult_fact
            self._page_size = 256
        else:
            self._boot_size = 512 * mult_fact
            self._page_size = 128

        self._chip_name = name
        self._flash_length = flash
        self._eeprom_length = eeprom

    @property
    def version(self):
        return self._version

    @property
    def page_size(self):
        return self._page_size

    @property
    def flash_length(self):
        return self._flash_length

    @property
    def boot_size(self):
        return self._boot_size

    @property
    def application_size(self):
        return self._flash_length - self._boot_size

    @property
    def eeprom_length(self):
        return self._eeprom_length

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

    def erase_page(self, address):
        self.write(self._flash_erase_packet(address))
        self.read()

    def write_flash_page(self, address, data):
        assert(address+self.page_size <= self.application_size)
        assert(len(data) <= self.page_size)

        self.erase_page(address)

        chunks = self._make_chunks(data, SPM_PAYLOAD_SIZE)
        for (i, chunk) in enumerate(chunks):
            self.write(self._temporary_buffer_packet(
                address + i*SPM_PAYLOAD_SIZE,
                chunk
            ))
            self.read()

        self.write(self._flash_write_packet(address))
        self.read()

    def erase_application_flash(self):
        for pg_num in range(self.application_size // self.page_size):
            self.erase_page(pg_num * self.page_size)

    # def write_flash(self, start_address, data):
    #     assert(start_address + len(data) <= self.application_size)

    def write_eeprom(self, start_address, data):
        assert(start_address + len(data) <= self.eeprom_length)


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


    def write_flash_hex(self, flash_file):
        flash_hex = IntelHex()
        flash_hex.fromfile(flash_file, "hex")

        if flash_hex.maxaddr() >= self.application_size:
            raise KpBoot32u4Error(
                "Hex file doesn't fit in flash. Maximum flash address is {}, but"
                " the given file writes to address {}.".format(
                    self.application_size,
                    flash_hex.maxaddr(),
                )
            )

        segments = flash_hex.segments()

        # checks if a given page is a part of any of the segments in the hex
        # file
        def is_page_used(p_start, p_end):
            for (seg_start, seg_end) in segments:
                if seg_start <= p_start < seg_end:
                    return True
                if seg_start <= p_end < seg_end:
                    return True
            return False

        # flash is only page accessible, so look at each page in the hex file
        # and see if it needs to be written
        for start in range(0, self.application_size, self.page_size):
            end = start+self.page_size
            if not is_page_used(start, end):
                continue
            # Get the data for the current page and write it
            data = bytearray(flash_hex.tobinstr(start, end-1))
            self.write_flash_page(start, data)

    def write_eeprom_hex(self, eep_file):
        eep_hex = IntelHex()
        eep_hex.fromfile(eep_file, "hex")

        segments = eep_hex.segments()

        # eeprom is byte addressable, so write all the bytes in each segment
        for (start, end) in segments:
            data = bytearray(eep_hex.tobinstr(start, end-1))
            self.write_eeprom(start, data)


if __name__ == "__main__":


    dev = find_devices()[0]

    dev.open()
    # for i in range(32):
    #     dev.write_flash_page(0x4000 + i*128, [i]*128)
    # for i in range(10):
    #     dev.write_flash_page(0x1000 + i*128, list(range(128)))
    # for i in range(10):
    #     dev.write_flash_page(0x1000 + i*128, [0xff]*128)

    # dev.write_eeprom(0x0100, list(range(128)))
    # dev.write_eeprom(0x0180, [0xAA]*64)
    # dev.write_eeprom(0x01C0, [0xBB]*64)
    # dev.write_eeprom(0x0200, [0xCC]*64)
    # dev.write_eeprom(0x0240, [0xDD]*64)
    # dev.write_eeprom(0x0280, [0xEE]*64)
    # dev.write_eeprom(0x02C0, [0xFF]*64)


    # dev.reset_mcu()

    dev.write_flash_hex("../../build/default-atmega32u4/keyplus_32u4-default-atmega32u4-1key.hex")
    # dev.write_eeprom_hex("eeprom.hex")

    dev.close()
