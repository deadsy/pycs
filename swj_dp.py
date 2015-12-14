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
_IR_DPACC = 0xa
_IR_APACC = 0xb
_IR_IDCODE = 0xe
_IR_BYPASS = 0xf

# lengths of data registers
_DR_ABORT_LEN = 35
_DR_DPACC_LEN = 35
_DR_APACC_LEN = 35
_DR_IDCODE_LEN = 32
_DR_BYPASS_LEN = 1

#-----------------------------------------------------------------------------
# Debug Port (DPACC) Registers

_DP_REG_CTRL_STAT = (1 << 1)
_DP_REG_SELECT    = (2 << 1)
_DP_REG_RDBUF     = (3 << 1)

_DP_WR = (0 << 0)
_DP_RD = (1 << 0)

#-----------------------------------------------------------------------------
# Access Port (APACC) Registers

_AP_REG_CSW = 0x00
_AP_REG_TAR = 0x04
_AP_REG_DRW = 0x0c
_AP_REG_BD0 = 0x10
_AP_REG_BD1 = 0x14
_AP_REG_BD2 = 0x18
_AP_REG_BD3 = 0x1c
_AP_REG_CFG = 0xf4
_AP_REG_BASE = 0xf8
_AP_REG_IDR = 0xfc

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

  def rw_dr(self, n, val = 0):
    """read/write n bits from the current dr register"""
    wr = bits.bits(n, val)
    rd = bits.bits(n)
    self.device.rw_dr(wr, rd)
    return rd.scan((n,))[0]

  def rd_idcode(self):
    """read the idcode"""
    self.wr_ir(_IR_IDCODE)
    return self.rw_dr(_DR_IDCODE_LEN)

  def wr_abort(self, val):
    """write abort register"""
    self.wr_ir(_IR_ABORT)
    self.device.wr_dr(bits.bits(_DR_ABORT_LEN, val))

  def rw_dpacc(self, val = 0):
    """read and write the dpacc register"""
    return self.rw_dr(_DR_DPACC_LEN, val)

  def rd_ctrl_stat(self):
    self.wr_ir(_IR_DPACC)
    x = self.rw_dpacc(_DP_REG_CTRL_STAT | _DP_WR)
    print('%x' % x)
    x = self.rw_dpacc()
    print('%x' % x)
    x = self.rw_dpacc(_DP_REG_SELECT | _DP_WR)
    print('%x' % x)
    x = self.rw_dpacc()
    print('%x' % x)
    x = self.rw_dpacc(_DP_REG_RDBUF | _DP_WR)
    print('%x' % x)
    x = self.rw_dpacc()
    print('%x' % x)

    return 0



#-----------------------------------------------------------------------------

class sw_dp:
  """Serial Wire Debug Port"""

  def __init__(self, device):
    self.device = device

#-----------------------------------------------------------------------------
