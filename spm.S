#include <avr/io.h>

#define IO_(x)  _SFR_IO_ADDR(x)

; ---
; Waits for the current SPM operation to finish executing.
;
; Input:
;     Nothing.
;
; Returns:
;     Nothing.
; ---

.section .boot_extra,"ax",@progbits
.global call_spm

call_spm:
	OUT	IO_(SPMCSR), r20	; r18 decides function
	SPM				; Store program memory
	_wait_spm_bit:
	in	r20, IO_(SPMCSR)	; get SPMCR into r18
	sbrc	r20, SPMEN
	rjmp	_wait_spm_bit		; Wait for SPMEN flag cleared
	ret
