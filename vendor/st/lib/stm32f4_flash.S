//-----------------------------------------------------------------------------
/*

stm32f4 flash loader: 32-bit flash writes

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

// FLASH.CR bits
#define CR_PG                (1 << 0) // Programming
#define CR_PSIZE_BYTE        (0 << 8) // 8 bits
#define CR_PSIZE_HALF_WORD   (1 << 8) // 16 bits
#define CR_PSIZE_WORD        (2 << 8) // 32 bits
#define CR_PSIZE_DOUBLE_WORD (3 << 8) // 64 bits

// FLASH.SR bits
#define SR_BSY    (1 << 16) // Busy
#define SR_RDERR  (1 << 8)  // Read error
#define SR_PGSERR (1 << 7)  // Programming sequence error
#define SR_PGPERR (1 << 6)  // Programming parallelism error
#define SR_PGAERR (1 << 5)  // Programming alignment error
#define SR_WRPERR (1 << 4)  // Write protection error
#define SR_OPERR  (1 << 1)  // Operation error
#define SR_EOP    (1 << 0)  // End of operation

#define SR_ERR (SR_RDERR | SR_PGSERR | SR_PGPERR | SR_PGAERR | SR_WRPERR | SR_OPERR)

// r0 = src address in ram, return code (ok == 0)
// r1 = dst address in flash
// r2 = number of u32 words to write

// r3 = tmp
// r4 = flash base
// r5 = status bits

start:
  ldr   r4, FLASH_BASE
  ldr   r5, SR_CLR

wr32:
  ldr   r3, CR_PG_U32
  str   r3, [r4, #CR]
  // 32-bit copy from ram to flash
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
  ands  r3, #SR_ERR
  bne   exit
  // next write
  subs  r2, #1
  bne   wr32

exit:
  mov   r0, r3
  bkpt  #0

.align 2

FLASH_BASE:
  .word 0x40023c00
CR_PG_U32:
  .word (CR_PG | CR_PSIZE_WORD)
SR_CLR:
  .word (SR_ERR | SR_EOP)

//-----------------------------------------------------------------------------
