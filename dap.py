#------------------------------------------------------------------------------
"""

CMSIS-DAP Driver

"""
#------------------------------------------------------------------------------

#import struct
#from array import array as Array

import usbdev
#import cortexm
#import iobuf

#------------------------------------------------------------------------------
# supported devices

dap_devices = (
  (0x0d28, 0x0204, 1), # NXP MIMXRT1020-EVK
)

def itf_lookup(vid, pid):
  """return the interface to use for a given device"""
  for (v, p, i) in dap_devices:
    if (v == vid) and (p == pid):
      return i
  return None

def find(vps=None, sn=None):
  """find an cmsis-dap device based on vid, pid and serial number"""
  if vps is None:
    # look for any dap device
    vps = [(vid, pid) for (vid, pid, itf) in dap_devices]
  return usbdev.find(vps, sn)


#------------------------------------------------------------------------------
# map register names to cmsis-dap register numbers

regmap = {
  'r0':0, 'r1':1, 'r2':2, 'r3':3, 'r4':4, 'r5':5, 'r6':6, 'r7':7,
  'r8':8, 'r9':9, 'r10':10, 'r11':11, 'r12':12, 'r13':13, 'r14':14, 'r15':15,
  'lr':14, 'pc':15, 'psr':16, 'msp':17, 'psp':18,
  # primask
  # faultmask
  # basepri
  # control
  # 19 ?
  # 20 ?
}

#------------------------------------------------------------------------------

class dap:
  """CMSIS-DAP Device Driver"""

  def __init__(self, vid, pid, sn):
    self.vid = vid
    self.pid = pid
    self.sn = sn
    itf = itf_lookup(self.vid, self.pid)
    self.usb = usbdev.usbdev()
    self.usb.open(self.vid, self.pid, interface=itf, serial=self.sn)

  def __del__(self):
    if self.usb is not None:
      self.close()

  def close(self):
    """close the usb interface"""
    self.usb.close()
    self.usb = None

  def rd_reg(self, n):
    """read from a register"""
    # TODO
    return 0

  def wr_reg(self, n, val):
    """write to a register"""
    # TODO

  def rd_mem8(self, adr, n):
    """read n 8-bit values from memory region"""
    # TODO
    return [0 for i in range(n)]

  def rd_mem16(self, adr, n):
    """read n 16-bit values from memory region"""
    assert adr & 1 == 0
    # TODO
    return [0 for i in range(n)]

  def rd_mem32(self, adr, n):
    """read n 32-bit values from memory region"""
    assert adr & 3 == 0
    # TODO
    return [0 for i in range(n)]

  def __str__(self):
    """return a string for basic device description"""
    s = []
    s.append('CMSIS-DAP usb %04x:%04x serial %r' % (self.vid, self.pid, self.sn))
    #s.append('target voltage %.3fV' % (float(self.get_voltage()) / 1000.0))
    return '\n'.join(s)

#------------------------------------------------------------------------------

class dbgio:
  """CMSIS-DAP implementation of dbgio cpu interface"""

  def __init__(self, vid=None, pid=None, idx=None, sn=None):
    """no actual operations, record the selected usb device"""
    self.vid = vid
    self.pid = pid
    self.idx = idx
    self.sn = sn
    self.cpu_name = None
    self.itf = None
    self.menu = (
      ('info', self.cmd_info),
    )

  def connect(self, cpu_name, itf):
    """connect the debugger to the target"""
    self.cpu_name = cpu_name
    self.dbg_itf = itf
    self.dap = dap(self.vid, self.pid, self.sn)

  def disconnect(self):
    """disconnect the debugger from the target"""
    self.dap.close()

  def cmd_info(self, ui, args):
    """display cmsis-dap information"""
    ui.put('%s\n' % self)

  def is_halted(self):
    """return True if target is halted"""
    # TODO
    return True

  def rdreg(self, reg):
    """read from the named register"""
    n = regmap.get(reg, None)
    if n is None:
      return None
    return self.dap.rd_reg(n)

  def wrreg(self, reg, val):
    """write to the named register"""
    n = regmap.get(reg, None)
    if n is None:
      return
    self.dap.wr_reg(n, val)

  def rdmem32(self, adr, n, io):
    """read n 32-bit words from memory starting at adr"""
    max_n = 0x20
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      _ = [io.wr32(x) for x in self.dap.rd_mem32(adr, nread)]
      n -= nread
      adr += nread * 4

  def rdmem16(self, adr, n, io):
    """read n 16-bit words from memory starting at adr"""
    max_n = 0x20
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      _ = [io.wr16(x) for x in self.dap.rd_mem16(adr, nread)]
      n -= nread
      adr += nread * 2

  def rdmem8(self, adr, n, io):
    """read n 8-bit words from memory starting at adr"""
    # n = 0..0x3c (ok), 0x3d..0x40 (slow), >= 0x41 (fails)
    max_n = 0x20
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      _ = [io.wr8(x) for x in self.dap.rd_mem8(adr, nread)]
      n -= nread
      adr += nread

  def rdmem(self, adr, n, io):
    """read a buffer from memory starting at adr"""
    if io.has_wr(32):
      self.rdmem32(adr, n, io)
    elif io.has_wr(16):
      self.rdmem16(adr, n, io)
    elif io.has_wr(8):
      self.rdmem8(adr, n, io)
    else:
      assert False, 'bad buffer width'

  def rd32(self, adr):
    """read 32 bit value from adr"""
    return self.dap.rd_mem32(adr, 1)[0]

  def rd16(self, adr):
    """read 16 bit value from adr"""
    return self.dap.rd_mem16(adr, 1)[0]

  def rd8(self, adr):
    """read 8 bit value from adr"""
    return self.dap.rd_mem8(adr, 1)[0]

  def __str__(self):
    return str(self.dap)


#------------------------------------------------------------------------------
