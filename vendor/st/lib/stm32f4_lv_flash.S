//-----------------------------------------------------------------------------
/*

stm32f4 low voltage flash loader

Under low voltage conditions we do 8-bit flash writes instead
of 32-bit writes.

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
  lsls  r2, r2, #2
  ldr   r3, FLASH_BASE

next:
  cbz   r2, exit
  ldrb  r4, [r0]
  strb  r4, [r1]

wait:
  ldrh  r4, [r3, #0x0e]
  tst.w r4, #1
  bne   wait
  add   r0, #1
  add   r1, #1
  sub   r2, #1
  b     next

exit:
  bkpt #0

.align 2

FLASH_BASE:
  .word 0x40023c00

//-----------------------------------------------------------------------------
