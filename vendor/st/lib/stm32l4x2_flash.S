//-----------------------------------------------------------------------------
/*

stm32l4x2 flash programmer

This chip programs the flash 64 bits at a time. We assume we have an integral
number of u64 words in the passed ram buffer. If that isn't true there might be
junk programmed at the end of the buffer write.

*/
//-----------------------------------------------------------------------------

.text
.syntax unified
.cpu cortex-m4
.thumb
.thumb_func
.global write

// register offsets
#define CR 0x14
#define SR 0x10

// Flash.CR bits
#define CR_FSTPG (1 << 18 ) // Fast programming
#define CR_PG (1 << 0)      // Programming

// Flash.SR bits
#define SR_BSY (1 << 16)      // Busy
#define SR_OPTVERR (1 << 15)  // Option validity error
#define SR_RDERR (1 << 14)    // PCROP read error
#define SR_FASTERR (1 << 9)   // Fast programming error
#define SR_MISERR (1 << 8)    // Fast programming data miss error
#define SR_PGSERR (1 << 7)    // Programming sequence error
#define SR_SIZERR (1 << 6)    // Size error
#define SR_PGAERR (1 << 5)    // Programming alignment error
#define SR_WRPERR (1 << 4)    // Write protected error
#define SR_PROGERR (1 << 3)   // Programming error
#define SR_OPERR (1 << 1)     // Operation error
#define SR_EOP (1 << 0)       // End of operation

#define SR_ERR (SR_OPTVERR|SR_RDERR|SR_FASTERR|SR_MISERR|SR_PGSERR|SR_SIZERR|SR_PGAERR|SR_WRPERR|SR_PROGERR|SR_OPERR)

// r0 = src address in ram, return code (ok == 0)
// r1 = dst address in flash
// r2 = number of u32 words to write

// r3 = tmp
// r4 = flash base
// r5 = status bits

start:
  ldr   r4, FLASH_BASE
  ldr   r5, SR_CLR
  // convert r2 to the number of 64-bit words
  lsr   r2, #1

wr64:
  // set the programming bit
  mov   r3, #CR_PG
  str   r3, [r4, #CR]
  // 64-bit copy from ram to flash
  ldr   r3, [r0], #4
  str   r3, [r1], #4
  ldr   r3, [r0], #4
  str   r3, [r1], #4

wait:
  // wait for programming completion
  ldr		r3, [r4, #SR]
  tst   r3, #SR_BSY
  bne   wait
  // clear the status bits
  str   r5, [r4, #SR]
  // check for errors
  bic   r3, #SR_EOP
  ands  r3, r5
  bne   exit
  // next write
  subs  r2, #1
  bne   wr64

exit:
  mov   r0, r3
  bkpt  #0

.align 2

FLASH_BASE:
  .word 0x40022000
SR_CLR:
  .word (SR_ERR | SR_EOP)

//-----------------------------------------------------------------------------


