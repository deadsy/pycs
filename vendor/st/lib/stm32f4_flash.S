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

// r0 = src address in ram
// r1 = dst address in flash
// r2 = number of u32 words
// r3 = flash base
// r4 = tmp

start:
  ldr r3, FLASH_BASE

next:
  cbz r2, exit
  ldr r4, [r0]
  str r4, [r1]

wait:
  ldrh  r4, [r3, #0x0e]
  tst.w r4, #1
  bne   wait
  add   r0, #4
  add   r1, #4
  sub   r2, #1
  b     next

exit:
  bkpt  #0

.align 2

FLASH_BASE:
  .word 0x40023c00

//-----------------------------------------------------------------------------


#if 0

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





.global start
.syntax unified

@ r0 = source
@ r1 = target
@ r2 = wordcount
@ r3 = flash_base
@ r4 = temp

start:
    ldr     r3, flash_base
next:
    cbz     r2, done
    ldr     r4, [r0]
    str     r4, [r1]

wait:
    ldrh    r4, [r3, #0x0e]
    tst.w   r4, #1
    bne     wait

    add     r0, #4
    add     r1, #4
    sub     r2, #1
    b       next
done:
    bkpt

.align 2

flash_base:
	.word 0x40023c00


    static const uint8_t loader_code_stm32f4[] = {
        // flashloaders/stm32f4.s

        0x07, 0x4b,

        0x62, 0xb1,
        0x04, 0x68,
        0x0c, 0x60,

        0xdc, 0x89,
        0x14, 0xf0, 0x01, 0x0f,
        0xfb, 0xd1,
        0x00, 0xf1, 0x04, 0x00,
        0x01, 0xf1, 0x04, 0x01,
        0xa2, 0xf1, 0x01, 0x02,
        0xf1, 0xe7,

        0x00, 0xbe,

        0x00, 0x3c, 0x02, 0x40,
    };

#endif


//-----------------------------------------------------------------------------
