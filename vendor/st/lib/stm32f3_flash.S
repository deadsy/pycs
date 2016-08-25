//-----------------------------------------------------------------------------
/*

stm32f3 flash loader

*/
//-----------------------------------------------------------------------------

.text
.syntax unified
.cpu cortex-m4
.thumb
.thumb_func
.global write

// register offsets
#define CR 0x10
#define SR 0x0c

// Flash.CR bits
#define CR_PG (1 << 0)

// Flash.SR bits
#define SR_EOP (1 << 5)
#define SR_WRPRT (1 << 4)
#define SR_PGERR (1 << 2)
#define SR_BSY (1 << 0)

// r0 = src address in ram
// r1 = dst address in flash
// r2 = number of u16 words
// r3 = tmp
// r4 = flash base

start:
  ldr r4, FLASH_BASE
  add r4, r3

write_u16:
  movs  r3, #CR_PG
  str   r3, [r4, #CR]
  ldrh  r3, [r0], #2
  strh  r3, [r1], #2

busy:
  ldr  r3, [r4, #SR]
  tst  r3, #SR_BSY
  beq  busy
  tst  r3, #(SR_PGERR | SR_WRPRT)
  bne  exit
  subs r2, r2, #1
  bne  write_u16

exit:
  bkpt #0

.align 2

FLASH_BASE:
  .word 0x40022000

//-----------------------------------------------------------------------------
