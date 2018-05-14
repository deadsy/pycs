#-----------------------------------------------------------------------------
"""

ADIv5 JTAG Debug Port

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

ir_name = {
  _IR_ABORT: 'abort',
  _IR_DPACC: 'dpacc',
  _IR_APACC: 'apacc',
  _IR_IDCODE: 'idcode',
  _IR_BYPASS: 'bypass',
}

#-----------------------------------------------------------------------------

# ACK[2:0]
_ACK_OK_FAULT = 2
_ACK_WAIT = 1

# RnW[0]
_DP_WR = 0
_DP_RD = 1

#-----------------------------------------------------------------------------
# Debug Port Register Access (DPACC)

_DPACC_CTRL_STAT = 0x4 # read/write
_DPACC_SELECT = 0x8 # read/write
_DPACC_RDBUFF = 0xc # read only

dpacc_name = {
  _DPACC_CTRL_STAT: 'ctrl/stat',
  _DPACC_SELECT: 'select',
  _DPACC_RDBUFF: 'rdbuff',
}

#-----------------------------------------------------------------------------
# ABORT Register

_ABORT_ORUNERRCLR = (1 << 4) # Clear the STICKYORUN flag, SW-DP only
_ABORT_WDERRCLR = (1 << 3) # Clear the WDATAERR flag, SW-DP only
_ABORT_STKERRCLR = (1 << 2) # Clear the STICKYERR flag, SW-DP only
_ABORT_STKCMPCLR = (1 << 1) # Clear the STICKYCMP flag, SW-DP only
_ABORT_DAPABORT = (1 << 0) # Generate a DAP abort

#-----------------------------------------------------------------------------
# DPACC CTRL/STAT register

CS_ORUNDETECT = (1 << 0)
CS_STICKYORUN = (1 << 1)
# 3:2 - transaction mode (e.g. pushed compare)
CS_STICKYCMP = (1 << 4)
CS_STICKYERR = (1 << 5)
CS_READOK = (1 << 6) # SWD-only
CS_WDATAERR = (1 << 7) # SWD-only
# 11:8 - mask lanes for pushed compare or verify ops
# 21:12 - transaction counter
CS_DBGRSTREQ = (1 << 26)
CS_DBGRSTACK = (1 << 27)
CS_DBGPWRUPREQ = (1 << 28) # debug power up request
CS_DBGPWRUPACK = (1 << 29) # debug power up acknowledge (read only)
CS_SYSPWRUPREQ = (1 << 30) # system power up request
CS_SYSPWRUPACK = (1 << 31) # system power up acknowledge (read only)

CS_PWR_REQ = CS_DBGPWRUPREQ | CS_SYSPWRUPREQ
CS_PWR_ACK = CS_DBGPWRUPACK | CS_SYSPWRUPACK
CS_ERR = CS_STICKYORUN | CS_STICKYCMP | CS_STICKYERR

#-----------------------------------------------------------------------------

class jtag_dp_error(IOError):
  """Error with JTAG-DP"""

class jtag_dp(object):
  """JTAG Debug Port"""

  def __init__(self, device):
    self.device = device
    self.ir = None
    # clear the sticky error bits
    self.wr_dpacc(_DPACC_CTRL_STAT, CS_ERR)
    # enable the power domains
    self.wr_dpacc(_DPACC_CTRL_STAT, CS_PWR_REQ)
    # wait for the power domains to activate
    while True:
      val = self.rd_dpacc(_DPACC_CTRL_STAT)
      if val & CS_PWR_ACK:
        break
    # enable the OVERRUN checking
    self.wr_dpacc(_DPACC_CTRL_STAT, CS_PWR_REQ | CS_ORUNDETECT)

  def wr_ir(self, ir):
    """write instruction register"""
    if self.ir == ir:
      # no changes
      return
    #print('ir[%s]' % ir_name[ir])
    self.device.wr_ir(bits.from_val(ir, _IR_LEN))
    self.ir = ir

  def rd_idcode(self):
    """read the idcode"""
    self.wr_ir(_IR_IDCODE)
    return self.device.rw_dr(bits.zeroes(_DR_IDCODE_LEN)).split((32,))[0]

  def wr_abort(self, val):
    """write abort register"""
    self.wr_ir(_IR_ABORT)
    self.device.wr_dr(bits.from_val(val, _DR_ABORT_LEN))

  def rw_dpacc(self, rnw, adr, val):
    """write to and readback from a dpacc register"""
    x = (val << 3) | ((adr >> 1) & 0x06) | rnw
    self.wr_ir(_IR_DPACC)
    rd = self.device.rw_dr(bits.from_val(x, _DR_DPACC_LEN))
    ack, val = rd.split((3, 32))
    if ack == _ACK_WAIT:
      raise jtag_dp_error('JTAG-DP ACK timeout')
    if ack != _ACK_OK_FAULT:
      raise jtag_dp_error('JTAG-DP invalid ACK')
    return val

  def rw_apacc(self, rnw, adr, val):
    """write to and readback from the selected apacc register"""
    x = (val << 3) | ((adr >> 1) & 0x06) | rnw
    self.wr_ir(_IR_APACC)
    rd = self.device.rw_dr(bits.from_val(x, _DR_APACC_LEN))
    ack, val = rd.split((3, 32))
    if ack == _ACK_WAIT:
      raise jtag_dp_error('JTAG-DP ACK timeout')
    if ack != _ACK_OK_FAULT:
      raise jtag_dp_error('JTAG-DP invalid ACK')
    return val

  def error(self):
    """clear and return the error bits from the control/status register"""
    self.rw_dpacc(_DP_RD, _DPACC_CTRL_STAT, 0)
    x = self.rw_dpacc(_DP_WR, _DPACC_CTRL_STAT, CS_PWR_REQ | CS_ORUNDETECT | CS_ERR)
    return x & CS_ERR

  def rd_dpacc(self, adr):
    """read a DPACC register"""
    self.rw_dpacc(_DP_RD, adr, 0)
    return self.rw_dpacc(_DP_RD, adr, 0)

  def wr_dpacc(self, adr, val):
    """write a DPACC register"""
    self.rw_dpacc(_DP_WR, adr, val)

  def wr_dpacc_select(self, ap, reg, dp=0):
    """write the DPACC select register"""
    x = ((ap & 0xff) << 24) | (reg & 0xf0) | (dp & 0xf)
    self.wr_dpacc(_DPACC_SELECT, x)

  def rd_rdbuff(self):
    """return the RDBUFF value"""
    return self.rw_dpacc(_DP_RD, _DPACC_RDBUFF, 0)

  def rd_apacc(self, ap, adr):
    """select the AP and read an APACC register"""
    self.wr_dpacc_select(ap, adr)
    self.rw_apacc(_DP_RD, adr, 0)
    return self.rw_apacc(_DP_RD, adr, 0)

  def wr_apacc(self, ap, adr, val):
    """select the AP and write an APACC register"""
    self.wr_dpacc_select(ap, adr)
    self.rw_apacc(_DP_WR, adr, val)

#-----------------------------------------------------------------------------
