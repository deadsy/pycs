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

// r0 = src address in ram, return code (ok == 0)
// r1 = dst address in flash
// r2 = number of u32 words to write

// r3 = tmp
// r4 = flash base
// r5 = status bits

start:
  ldr   r4, FLASH_BASE
  lsl   r2, #1
  mov   r5, #(SR_EOP | SR_WRPRT | SR_PGERR)

wr16:
  // set the programming bit
  mov   r3, #CR_PG
  str   r3, [r4, #CR]
  // 16 bit copy from ram to flash
  ldrh  r3, [r0], #2
  strh  r3, [r1], #2

wait:
  // wait for programming completion
  ldr		r3, [r4, #SR]
  tst   r3, #SR_BSY
  bne   wait
  // clear the status bits
  str   r5, [r4, #SR]
  // check for errors
  ands  r3, #(SR_PGERR | SR_WRPRT)
  bne   exit
  // next write
  subs  r2, #1
  bne   wr16

exit:
  mov   r0, r3
  bkpt  #0

.align 2

FLASH_BASE:
  .word 0x40022000

//-----------------------------------------------------------------------------


