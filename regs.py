# -----------------------------------------------------------------------------
"""

Register and Register Sets

"""
# ----------------------------------------------------------------------------
# register bit fields

class fld(object):

  def __init__(self, name, msb, lsb, fmt=None):
    self.name = name
    self.msb = msb
    self.lsb = lsb
    self.fmt = fmt
    # derived values
    self.mask = ((1 << (self.msb - self.lsb + 1)) - 1) << self.lsb

  def emit(self, val):
    val = (val & self.mask) >> self.lsb
    if self.msb == self.lsb:
      name = '%s[%d]' % (self.name, self.lsb)
    else:
      name = '%s[%d:%d]' % (self.name, self.msb, self.lsb)
    pad = ' ' * 4
    if self.fmt:
      if callable(self.fmt):
        val_str = self.fmt(val)
    else:
      if val < 10:
        val_str = '%d' % val
      else:
        val_str = '0x%x' % val
    return '%s%-29s: %s' % (pad, name, val_str)

class fld_set(object):

  def __init__(self, name, flds):
    self.name = name
    self.flds = flds

  def emit(self, val):
    s = []
    for fld in self.flds:
      s.append(fld.emit(val))
    return '\n'.join(s)

# -----------------------------------------------------------------------------
# memory mapped registers

class memreg(object):
  """generic memory mapped register"""

  def __init__(self, name, ofs, fields = False):
    self.name = name
    self.ofs = ofs
    self.fields = fields

  def adr(self, base, idx):
    return base + self.ofs + (idx * (self.width / 8))

  def rd(self, cpu, base, idx):
    return cpu.rd(self.adr(base, idx), self.width)

  def wr(self, cpu, base, val, idx):
    return cpu.wr(self.adr(base, idx), val, self.width)

  def emit(self, cpu, base):
    adr = self.adr(base, 0)
    val = cpu.rd(adr, self.width)
    s = []
    s.append('%-32s : ' % self.name)
    s.append('0x%08x' % adr)
    s.append('[%d:0] = ' % (self.width - 1))
    if val == 0:
      s.append('0')
    else:
      fmt = '0x%%0%dx' % (self.width / 4)
      s.append(fmt % val)
    s = ''.join(s)
    if self.fields:
      return '%s\n%s' % (s, self.fields.emit(val))
    return s

class reg8(memreg):
  """8-bit memory mapped register"""
  width = 8

class reg16(memreg):
  """16-bit memory mapped register"""
  width = 16

class reg32(memreg):
  """32-bit memory mapped register"""
  width = 32

# -----------------------------------------------------------------------------

class memio(object):
  """bind a register set to a specific cpu/address"""

  def __init__(self, cpu, base, regs):
    self.cpu = cpu
    self.base = base
    self.regs = regs

  def rd(self, name, idx = 0):
    return self.regs.name2reg[name].rd(self.cpu, self.base, idx)

  def wr(self, name, val, idx = 0):
    return self.regs.name2reg[name].wr(self.cpu, self.base, val, idx)

# -----------------------------------------------------------------------------

class regset(object):

  def __init__(self, name, regs):
    self.name = name
    self.regs = regs
    # lookup the register by name
    self.name2reg = dict([(r.name, r) for r in regs])

  def emit(self, cpu, base):
    s = [reg.emit(cpu, base) for reg in self.regs if not reg.fields is None]
    return '\n'.join(s)

# -----------------------------------------------------------------------------
