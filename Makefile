# Copyright 2017 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

TARGET_BASE_NAME = kp_boot_32u4

ARCH = AVR8
F_CPU = 16000000

# Output format. (can be srec, ihex, binary)
FORMAT = ihex

USB_VID = 6666
USB_PID = 9999

VPATH += src
CFLAGS += -Isrc

#######################################################################
#                        board config options                         #
#######################################################################

BOARD_DIR = boards
BUILD_DIR = build

# Note: Specific board configs are stored in the `boards` directory.

ifndef BOARD
  BOARD = default
endif

# Look for the board appropriate board .mk file to include
AVR_MK_FILE_DIR = ./avr-makefile
include $(AVR_MK_FILE_DIR)/boards.mk

#######################################################################
#                       include other makefiles                       #
#######################################################################

include avr-makefile/avr-mega.mk

include src/usb/usb.mk

#######################################################################
#                         programmer options                          #
#######################################################################

AVRDUDE_PROGRAMMER = usbasp
AVRDUDE_CMD = avrdude -p $(MCU) -c $(AVRDUDE_PROGRAMMER)

#######################################################################
#                           compiler setup                            #
#######################################################################

CFLAGS += -Wno-error=unused-function
# CFLAGS += -Wl,-verbose

# CFLAGS += -DUSE_KEYBOARD_TEST=1

# List C source files here.
C_SRC += \
	main.c \
	usb.c

# List Assembler source files here.
# NOTE: Use *.S for user written asm files. *.s is used for compiler generated
ASM_SRC = \
	spm.S \

# Optimization level, can be [0, 1, 2, 3, s].
OPT = s

# List any extra directories to look for include files here.
EXTRAINCDIRS =

# Compiler flag to set the C Standard level.
CSTANDARD = -std=gnu99

CDEFS +=
ADEFS +=

CFLAGS += -DBOOT_SIZE=BOOT_SIZE_$(BOOTSZ)
CFLAGS += -DCHIP_ID=CHIP_ID_$(MCU_STRING)

# Position the spm_call function at the very end of flash/bootloader
SPM_CALL_SIZE = 16
# SPM_CALL_POS = $(shell python -c "print( hex(\ $(FLASH_SIZE)-$(SPM_CALL_SIZE)\) )")
# BOOT_SECTION_START = $(shell python -c "print( hex(\$(FLASH_SIZE)-$(BOOT_SIZE)\) )")
SPM_CALL_POS = $(shell python -c "print( hex( $(FLASH_SIZE)-$(SPM_CALL_SIZE)) )")
BOOT_SECTION_START = $(shell python -c "print( hex($(FLASH_SIZE)-$(BOOT_SIZE)) )")

# LD_SCRIPT_DIR = /usr/lib/ldscripts
LD_SCRIPT_DIR = ./ld_scripts

LD_SCRIPT = avr5.xn

LDFLAGS += -T $(LD_SCRIPT_DIR)/$(LD_SCRIPT)

LDFLAGS += -Wl,--section-start=.text=$(BOOT_SECTION_START)

LDFLAGS += -Wl,--section-start=.boot_extra=$(SPM_CALL_POS)
LDFLAGS += -Wl,--undefined=.boot_extra


# # 4kb
# LFUSE = 7F
# HFUSE = D8
# EFUSE = FB # --> EFUSE = F3

# 1kb
LFUSE = 7F
HFUSE = DC
EFUSE = CB

#######################################################################
#                               recipes                               #
#######################################################################


all: hex fuse

hex: Makefile

program-dfu: $(TARGET_HEX)
	dfu-programmer $(MCU) erase --force
	dfu-programmer $(MCU) flash $(TARGET_HEX)
	dfu-programmer $(MCU) start

include avr-makefile/avr.mk
include avr-makefile/avr-program.mk

# Listing of phony targets.
.PHONY : all begin finish end sizebefore sizeafter gccversion \
build elf hex eep lss sym coff extcoff doxygen clean program-fuses \
