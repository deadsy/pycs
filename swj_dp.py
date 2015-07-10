#-----------------------------------------------------------------------------
"""

SWJ-DP = JTAG-DP + SW-DP

"""
#-----------------------------------------------------------------------------

import bits

#-----------------------------------------------------------------------------
# JTAG-DP Registers

# length of instruction register
_IR_LEN = 4

# addresses of data registers
_IR_ABORT = 0x8
_IR_DPACC = 0xA
_IR_APACC = 0xB
_IR_IDCODE = 0xE

# lengths of data registers
_DR_ABORT_LEN = 35
_DR_DPACC_LEN = 35
_DR_APACC_LEN = 35
_DR_IDCODE_LEN = 32

#-----------------------------------------------------------------------------
# ABORT Register

_ABORT_ORUNERRCLR = (1 << 4) # Clear the STICKYORUN flag, SW-DP only
_ABORT_WDERRCLR   = (1 << 3) # Clear the WDATAERR flag, SW-DP only
_ABORT_STKERRCLR  = (1 << 2) # Clear the STICKYERR flag, SW-DP only
_ABORT_STKCMPCLR  = (1 << 1) # Clear the STICKYCMP flag, SW-DP only
_ABORT_DAPABORT   = (1 << 0) # Generate a DAP abort

#-----------------------------------------------------------------------------

class jtag_dp:
  """JTAG Debug Port"""

  def __init__(self, device):
    self.device = device

  def wr_ir(self, val):
    """write instruction register"""
    wr = bits.bits(_IR_LEN, val)
    self.device.wr_ir(wr)

  def rd_dr(self, n):
    """read n bits from the current dr register"""
    wr = bits.bits(n)
    rd = bits.bits(n)
    self.device.rw_dr(wr, rd)
    return rd.scan((n,))[0]

  def rd_idcode(self):
    """read the idcode"""
    self.wr_ir(_IR_IDCODE)
    return self.rd_dr(_DR_IDCODE_LEN)

  def wr_abort(self, val):
    """write abort register"""
    self.wr_ir(_IR_ABORT)
    self.device.wr_dr(bits.bits(_DR_ABORT_LEN, val))

  def rd_dpacc(self):
    """read dpacc register"""
    self.wr_ir(_IR_DPACC)
    return self.rd_dr(_DR_DPACC_LEN)

  def rd_apacc(self):
    """read apacc register"""
    self.wr_ir(_IR_APACC)
    return self.rd_dr(_DR_APACC_LEN)

#-----------------------------------------------------------------------------

class sw_dp:
  """Serial Wire Debug Port"""

  def __init__(self, device):
    self.device = device

#-----------------------------------------------------------------------------
