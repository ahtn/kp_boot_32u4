
# kp_boot_32u4 USB HID bootloader for ATmega32u4 family of microcontrollers

A simple bootloader for the ATmega32u4 family of USB microcontrollers.
The code size is <1kB and doesn't need drivers on Windows.
Supports writing flash, eeprom, and lock bits.

It also exposes an `SPM` interface allowing firmware to write its own flash.

## cli interface

List the currently connected devices:
```sh
./kp_boot_32u4_cli.py -l
```

Program a firmware hex file:
```sh
./kp_boot_32u4_cli.py -f program.hex
```

Program an eeprom hex file:
```sh
./kp_boot_32u4_cli.py -E eeprom.hex
```

## Enter bootloader
Ways to enter the bootloader:

* 1. Push the reset button (short RST pin to GND) once. The device will then
  stay in bootloader mode until a firmware hex file is loaded, or the reset
  button is pushed a second time.  If no USB port is detected the device will
  automatically reset into the firmware application.
* 2. The firmware can enter the bootloader by setting a magic value and causing
  wdt reset. The bootloader will check for the value `0xda54` at the SRAM
  address and if it equals `0x01fc` the application code will be run.

## SPM interface

The bootloader has an SPM instruction with the appropriate support code to
allow firmware to update its own flash. The interface is always stored in
the last 16 bytes of flash at address. (TODO: add source code library
for common SPM commands).

```asm
; ---
; Performs an SPM command and waits for it to finish executing.
;
; Input:
;
; * r0:r1: optional data value used by SPM command
; * Z[r30:r31]: address used by SPM command
; * r10: spm command loaded into SPMCSR register
; * r11: spm command loaded into SPMCSR register. It should be used
;        to re-enable the RWW enable section after flash erase/write
;        operations by setting it equal to `(1<<SPMEN) | (1<<RWWSRE)`.
;        When writing to the temporary page buffer, it should be set
;        to 0 to perform no action.
;
; Returns:
;     Nothing.
; ---

.section .boot_extra,"ax",@progbits
.global call_spm

call_spm:
	out	IO_(SPMCSR), r10	; r18 decides function
	spm				; Store program memory

wait1:  in	r10, IO_(SPMCSR)	; get SPMCR into r18
	sbrc	r10, SPMEN
	rjmp	wait1			; Wait for SPMEN flag cleared

	out	IO_(SPMCSR), r11
	spm

; I don't think it is necessary to wait after re-enable RWW section
; wait2:  in	r10, IO_(SPMCSR)	; get SPMCR into r18
; 	sbrc	r10, SPMEN
; 	rjmp	wait2			; Wait for SPMEN flag cleared

finspm:
	ret
```
