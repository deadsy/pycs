#-----------------------------------------------------------------------------
"""

Cortex A53 Debug Components

Note 1: The "cortex a53" name is probably overly specific here.
Maybe it should be armv8 or aarch64 or something....

Note 2: I'm supporting the bcm49408 chip which Broadcom calls a "B53" and
says is derived from the "A53". Who knows what that means... but they have
changed the MIDR register from the A53 value.

"""
#-----------------------------------------------------------------------------

import logging
import adiv5

log = logging.getLogger(__name__)

#-----------------------------------------------------------------------------
# Instruction encodings for accessing the coprocessor interface

MCR = 0xee000010
MRC = 0xee100010

def CPREG(coproc, opc1, rt, crn, crm, opc2):
	return (opc1 << 21) | (crn << 16) | (rt << 12) | (coproc << 8) | (opc2 << 5) | crm

# Debug registers CP14
DBGDTRRXint = CPREG(14, 0, 0, 0, 5, 0)
DBGDTRTXint = CPREG(14, 0, 0, 0, 5, 0)

# Address translation registers CP15
PAR = CPREG(15, 0, 0, 7, 4, 0)
ATS1CPR = CPREG(15, 0, 0, 7, 8, 0)

# Cache management registers CP15
ICIALLU = CPREG(15, 0, 0, 7, 5, 0)
DCCIMVAC = CPREG(15, 0, 0, 7, 14, 1)
DCCMVAC = CPREG(15, 0, 0, 7, 10, 1)

#-----------------------------------------------------------------------------
# Debug Unit

# Section 11.7 of Cortex A-53 TRM, H9 of ARMv8 architecture reference manual
DBG_ECR = 0x024
DBG_WAR = 0x030 # 64 bits
DBG_DTRRX = 0x080 # data transfer register receive
DBG_ITR = 0x084 # instruction transfer register (wo)
DBG_SCR = 0x088 # status and control register
DBG_DTRTX = 0x08c # data transfer register transmit
DBG_RCR = 0x090 # reserve control register (wo)
DBG_OSLAR = 0x300
DBG_PRCR = 0x310
DBG_PRSR = 0x314
def DBG_BP(i, ofs): return 0x400 + (0x10 * i) + ofs # i = 0..5, debug breakpoints (BVR and BCR)
def DBG_WP(i, ofs): return 0x800 + (0x10 * i) + ofs # i = 0..3, debug watchpoints (WVR and WCR)
DBG_MIDR = 0xd00 # main id register
DBG_PFR =	0xd20 # processor feature, 64 bits, bits 28..63 are 0 on cortex-A53
DBG_DFR =	0xd28 # debug feature, 64 bits, bits 32..63 are 0 on cortex-A53
DBG_ISAR = 0xd30 # instruction set architecture feature, 64 bits, bits 20..63 are 0 on cortex-A53
DBG_MFR =	0xd38 # memory feature, 64 bits, bits 32..63 are 0 on cortex-A53
DBG_LAR = 0xfb0 # lock access
DBG_LSR = 0xfb4 # lock status (ro)
DBG_AUTHSTATUS = 0xfb8 # authentication status (el1, ro)

# SCR bits
SCR_STATUS = (0x3f <<  0)
SCR_ERR = (1 << 6)
SCR_A = (1 << 7)
SCR_EL = (3 << 8)
SCR_RW = (0xf << 10)
SCR_HDE = (1 << 14)
SCR_SDD = (1 << 16)
SCR_NS = (1 << 18)
SCR_SC2 = (1 << 19)
SCR_MA = (1 << 20)
SCR_TDA = (1 << 21)
SCR_INTdis = (3 << 22)
SCR_ITE = (1 << 24) # ITR empty
SCR_PipeAdv = (1 << 25)
SCR_TXU = (1 << 26)
SCR_RXO = (1 << 27)
SCR_ITO = (1 << 28)
SCR_DTR_TX_FULL = (1 << 29)
SCR_DTR_RX_FULL = (1 << 30)

OPCODE_TIMEOUT = 100 # milliseconds

class debug(object):

  def __init__(self, ap, base):
    self.ap = ap
    self.base = base
    self.scr = self.rd32(DBG_SCR)
    self.update_el(False)

    #self.exec_opcode(0)
    #log.info('midr 0x%08x' % self.rd32(DBG_MIDR))
    #log.info('pfr 0x%08x' % self.rd32(DBG_PFR))
    #log.info('isar 0x%08x' % self.rd32(DBG_ISAR))
    #log.info('mfr 0x%08x' % self.rd32(DBG_MFR))
    #log.info('dfr 0x%08x' % self.rd32(DBG_DFR))

  def rd32(self, reg):
    """read a 32 bit register"""
    self.ap.wr_apacc(adiv5.APACC_TAR, self.base + reg)
    self.ap.dp.rw_apacc(adiv5.AP_RD, adiv5.APACC_DRW, 0)
    return self.ap.dp.rd_rdbuff()

  def rd64(self, reg):
    """read a 64 bit register"""
    lo = self.rd32(reg)
    hi = self.rd32(reg + 4)
    return (hi << 32) | lo

  def wr32(self, reg, val):
    """write a 32 bit register"""
    self.ap.wr_apacc(adiv5.APACC_TAR, self.base + reg)
    self.ap.dp.rw_apacc(adiv5.AP_WR, adiv5.APACC_DRW, val)

  def in_aarch64(self):
    """return True if the core is in AArch64 mode"""
    el = (self.scr >> 8) & 3
    rw = (self.scr >> 10) & 0xf
    self.last_el = el
    return (rw >> el) & 1 != 0

  def update_el(self, msg=True):
    """update the cached eception level"""
    el = (self.scr >> 8) & 3
    if msg and self.last_el != el:
      log.info('EL %d->%d' % (self.last_el, el))
      self.last_el = el

  def wait4_ite(self, timeout=0):
    """wait for the SCR to indicate instruction completion"""
    # TODO - add timeout
    while self.scr & SCR_ITE == 0:
      self.scr = self.rd32(DBG_SCR)

  def exec_opcode(self, opcode):
    """execute an opcode"""
    self.wait4_ite(OPCODE_TIMEOUT)
    if self.in_aarch64():
      opcode = T32_FMTITR(opcode)
    self.wr32(DBG_ITR, opcode)
    self.wait4_ite(OPCODE_TIMEOUT)
    self.update_el()
    if self.scr & SCR_ERR:
      log.info('Opcode 0x%08x DSCR.ERR=1, DSCR.EL=%d' % (opcode, self.last_el))
      # TODO exception handling

  def rd_gpreg(self, regnum):
    """read a general purpose cpu register"""
    # To read a register we use DBGITR to load an MCR instruction
	  # that sends the value via DCC DBGDTRTX using the CP14 interface.
    ins = MCR | DBGDTRTXint | ((regnum & 0xf) << 12)
    self.wr32(DBG_ITR, ins)
    # Return value read from DCC channel
    return self.rd32(DBG_DTRTX)


  def __str__(self):
    return '%s Debug@0x%08x' % (self.ap.name(), self.base)


#-----------------------------------------------------------------------------
# Cross Trigger Interface (CTI)

class cti(object):

  def __init__(self, ap, base):
    self.ap = ap
    self.base = base

  def __str__(self):
    return '%s CTI@0x%08x' % (self.ap.name(), self.base)


#-----------------------------------------------------------------------------
# Performance Monitor Unit (PMU)

class pmu(object):

  def __init__(self, ap, base):
    self.ap = ap
    self.base = base

  def __str__(self):
    return '%s PMU@0x%08x' % (self.ap.name(), self.base)


#-----------------------------------------------------------------------------
# Embedded Trace Macrocell (ETM)

class etm(object):

  def __init__(self, ap, base):
    self.ap = ap
    self.base = base

  def __str__(self):
    return '%s ETM@0x%08x' % (self.ap.name(), self.base)


#-----------------------------------------------------------------------------
