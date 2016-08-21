//-----------------------------------------------------------------------------
/*

stm32f4 flash loader

*/
//-----------------------------------------------------------------------------

.text
.syntax unified
.cpu cortex-m4
.thumb
.thumb_func
.global write

// register offsets
#define ACR       0x00 // Flash access control register
#define KEYR      0x04 // Flash key register
#define OPTKEYR   0x08 // Flash option key register
#define SR        0x0c // Status register
#define CR        0x10 // Control register
#define OPTCR     0x14 // Flash option control register

// FLASH.SR bits
#define SR_BSY    (1 << 16) // Busy
#define SR_RDERR  (1 << 8)  // Read error
#define SR_PGSERR (1 << 7)  // Programming sequence error
#define SR_PGPERR (1 << 6)  // Programming parallelism error
#define SR_PGAERR (1 << 5)  // Programming alignment error
#define SR_WRPERR (1 << 4)  // Write protection error
#define SR_OPERR  (1 << 1)  // Operation error
#define SR_EOP    (1 << 0)  // End of operation

// r0 = src address in ram
// r1 = dst address in flash
// r2 = wordcount
// r3 = FLASH hardware control
// r4 = tmp

start:
  ldr     r3, FLASH_ADR

next:
  cbz     r2, exit
  ldr     r4, [r0]
  str     r4, [r1]

wait:

  ldr     r4, [r3, #SR]
  tst     r4, #SR_BSY
  bne     wait

  add     r0, #4
  add     r1, #4
  sub     r2, #1
  b       next

exit:
  bkpt #0

.align 2

FLASH_ADR:
  .word 0x40023c00

//-----------------------------------------------------------------------------
