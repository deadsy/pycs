# -----------------------------------------------------------------------------
"""

SoC Object

Takes an SVD file, parses it, and then re-expresses it as a python object
that matches the requirements of pycs. Typically the resulting data structures
will need some vendor/device specific tweaking to make up for things in the svd
file that are missing or wrong. These tweaks are done by the vendor specific SoC
code.

"""
# -----------------------------------------------------------------------------

import svd
import util

# -----------------------------------------------------------------------------

help_regs = (
  ('<cr>', 'display cpu registers'),
  ('[name]', 'display registers for peripheral')
)

# -----------------------------------------------------------------------------
# utility functions

def description_cleanup(s):
  """cleanup a description string"""
  if s is None:
    return None
  s = util.rm_non_ascii(s)
  s = s.strip('."')
  # remove un-needed white space
  return ' '.join([x.strip() for x in s.split()])

def name_cleanup(s):
  """cleanup a register name"""
  if s is None:
    return None
  s = s.replace('[%s]', '%s')
  return s

def sizeof_address_blocks(blocks, usage):
  """return the consolidated size (offset == 0) for a list of address blocks"""
  end = 0
  for b in blocks:
    if b.usage != usage:
      continue
    e = b.offset + b.size
    if e > end:
      end = e
  # return the size
  return end

def bitrange_string(s):
  """parse a string of the form [%d:%d]"""
  s = s.lstrip('[')
  s = s.rstrip(']')
  x = s.split(':')
  try:
    msb = int(x[0], 10)
    lsb = int(x[1], 10)
  except:
    return None
  return (msb, lsb)

# -----------------------------------------------------------------------------
# handle the dimElementGroup

def x_dash_y_string(s, n):
  """parse a string of the form %d-%d"""
  x = s.split('-')
  if len(x) != 2:
    return None
  try:
    a = int(x[0], 10)
    b = int(x[1], 10)
  except:
    return None
  if (b - a + 1) != n:
    # wrong length
    return None
  return (a, b)

def build_indices(dim, dimIndex):
  """return a list of strings for the register name indices"""
  if dim is None:
    return None

  if dimIndex is None:
    # Assume a simple 0..n index
    return ['%d' % i for i in range(dim)]

  # handle a comma delimited list
  x = dimIndex.split(',')
  # make sure we have enough indices
  if len(x) == dim:
    return x

  # look for strings of the form "%d-%d"
  x = x_dash_y_string(dimIndex, dim)
  if x is not None:
    return ['%d' % i for i in range(x[0], x[1] + 1)]

  # something else....
  assert False, 'unhandled dim %d dimIndex %s' % (dim, dimIndex)

# -----------------------------------------------------------------------------

def attribute_string(s):
  """return a python code string for a string variable"""
  if s is None:
    return 'None'
  # escape any ' characters
  s = s.replace("'", "\\'")
  return "'%s'" % s

def attribute_hex32(x):
  """return a python code string for a 32 bit hex value"""
  if x is None:
    return 'None'
  return '0x%08x' % x

def attribute_hex(x):
  """return a python code string for a hex value"""
  if x is None:
    return 'None'
  return '0x%x' % x

# -----------------------------------------------------------------------------

class interrupt(object):
  """interrupt information"""

  def __init__(self):
    self.name = None
    self.description = None
    self.irq = None
    self.parent = None

  def __str__(self):
    s = []
    s.append('i = soc.interrupt()')
    s.append('i.name = %s' % attribute_string(self.name))
    s.append('i.description = %s' % attribute_string(self.description))
    s.append('i.irq = %d' % self.irq)
    s.append('interrupts[%s] = i\n' % attribute_string(self.name))
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class enumval(object):
  """associate a name string with a bitfield value"""

  def __init__(self):
    self.name = None
    self.description = None
    self.value = None
    self.isDefault = None
    self.parent = None

  def __str__(self):
    s = []
    s.append('ev = soc.enumval()')
    s.append('ev.name = %s' % attribute_string(self.name))
    s.append('ev.description = %s' % attribute_string(self.description))
    s.append('ev.value = %d' % self.value)
    s.append('enumval[%d] = ev\n' % self.value)
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class enumvals(object):
  """a set of enumvals for a given register bitfield"""

  def __init__(self):
    self.name = None
    self.enumval = None
    self.usage = None
    self.parent = None

  def __str__(self):
    s = []
    if self.enumval is not None:
      # dump the enumerate values in name order
      s.append('enumval = {}')
      e_list = self.enumval.values()
      e_list.sort(key=lambda x: x.name)
      for e in e_list:
        s.append('%s' % e)
    s.append('e = soc.enumvals()')
    s.append('e.name = %s' % attribute_string(self.name))
    s.append('e.usage = %s' % attribute_string(self.usage))
    s.append('e.enumval = %s' % ('enumval', 'None')[self.enumval is None])
    s.append('enumvals.append(e)\n')
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class field(object):
  """information for a set of bits within a register"""

  def __init__(self):
    self.name = None
    self.description = None
    self.msb = None
    self.lsb = None
    self.enumvals = None
    self.parent = None
    self.fmt = None
    self.cached_val = None

  def field_name(self, val):
    """return the name for the field value"""
    mask = ((1 << (self.msb - self.lsb + 1)) - 1) << self.lsb
    val = (val & mask) >> self.lsb
    val_name = ''
    if callable(self.fmt):
      val_name = self.fmt(val)
    else:
      if self.enumvals is not None and len(self.enumvals) >= 1:
        # find the enumvals with usage 'read', or just find one
        for e in self.enumvals:
          if e.usage == 'read':
            break
        if val in e.enumval:
          val_name = e.enumval[val].name
    return val_name

  def display(self, val):
    """return display columns (name, val, '', descr) for this field"""
    mask = ((1 << (self.msb - self.lsb + 1)) - 1) << self.lsb
    val = (val & mask) >> self.lsb
    # work out if the value has changed since we last displayed it
    changed = '  '
    if self.cached_val is None:
      self.cached_val = val
    elif self.cached_val != val:
      self.cached_val = val
      changed = ' *'
    if self.msb == self.lsb:
      name = '  %s[%d]' % (self.name, self.lsb)
    else:
      name = '  %s[%d:%d]' % (self.name, self.msb, self.lsb)
    val_name = ''
    if callable(self.fmt):
      val_name = self.fmt(val)
    else:
      if self.enumvals is not None and len(self.enumvals) >= 1:
        # find the enumvals with usage 'read', or just find one
        for e in self.enumvals:
          if e.usage == 'read':
            break
        if val in e.enumval:
          val_name = e.enumval[val].name
    val_str = (': 0x%x %s%s' % (val, val_name, changed), ': %d %s%s' % (val, val_name, changed))[val < 10]
    return [name, val_str, '', self.description]

  def __str__(self):
    s = []
    if self.enumvals is not None:
      # dump the enumerate values in name order
      s.append('enumvals = []')
      e_list = self.enumvals
      e_list.sort(key=lambda x: x.usage)
      for e in e_list:
        s.append('%s' % e)
    s.append('f = soc.field()')
    s.append('f.name = %s' % attribute_string(self.name))
    s.append('f.description = %s' % attribute_string(self.description))
    s.append('f.msb = %d' % self.msb)
    s.append('f.lsb = %d' % self.lsb)
    s.append('f.enumvals = %s' % ('enumvals', 'None')[self.enumvals is None])
    s.append('fields[%s] = f\n' % attribute_string(self.name))
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class register(object):
  """a peripheral register"""

  def __init__(self):
    self.name = None
    self.description = None
    self.size = None
    self.offset = None
    self.fields = None
    self.parent = None
    self.cpu = None
    self.cached_val = None

  def __getattr__(self, name):
    """make the field name a class attribute"""
    return self.fields[name]

  def bind_cpu(self, cpu):
    """bind a cpu to the register"""
    self.cpu = cpu

  def adr(self, idx, size):
    return self.parent.address + self.offset + (idx * (size / 8))

  def rd(self, idx=0):
    return self.cpu.rd(self.adr(idx, self.size), self.size)

  def rd8(self, idx=0):
    return self.cpu.rd(self.adr(idx, 8), 8)

  def wr(self, val, idx=0):
    return self.cpu.wr(self.adr(idx, self.size), val, self.size)

  def set_bit(self, val, idx=0):
    self.wr(self.rd(idx) | val, idx)

  def clr_bit(self, val, idx=0):
    self.wr(self.rd(idx) & ~val, idx)

  def field_list(self):
    """return an ordered fields list"""
    # build a list of fields in most significant bit order
    f_list = self.fields.values()
    f_list.sort(key=lambda x: x.msb, reverse=True)
    return f_list

  def display(self, display_fields):
    """return display columns (name, adr, val, descr) for this register"""
    adr = self.adr(0, self.size)
    val = self.rd()
    # work out if the value has changed since we last displayed it
    changed = '  '
    if self.cached_val is None:
      self.cached_val = val
    elif self.cached_val != val:
      self.cached_val = val
      changed = ' *'
    adr_str = ': %08x[%d:0]' % (adr, self.size - 1)
    if val == 0:
      val_str = '= 0%s' % changed
    else:
      fmt = '= 0x%%0%dx%%s' % (self.size / 4)
      val_str = fmt % (val, changed)
    clist = []
    clist.append([self.name, adr_str, val_str, self.description])
    # output the fields
    if display_fields and self.fields:
      for f in self.field_list():
        clist.append(f.display(val))
    return clist

  def __str__(self):
    s = []
    if self.fields is not None:
      # dump the fields in most significant bit order
      s.append('fields = {}')
      f_list = self.fields.values()
      f_list.sort(key=lambda x: x.msb, reverse=True)
      for f in f_list:
        s.append('%s' % f)
    s.append('r = soc.register()')
    s.append('r.name = %s' % attribute_string(self.name))
    s.append('r.description = %s' % attribute_string(self.description))
    s.append('r.size = %d' % self.size)
    s.append('r.offset = 0x%x' % self.offset)
    s.append('r.fields = %s' % ('fields', 'None')[self.fields is None])
    s.append('registers[%s] = r\n' % attribute_string(self.name))
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class peripheral(object):
  """a set of registers for an SoC peripheral"""

  def __init__(self):
    self.name = None
    self.description = None
    self.address = None
    self.size = None
    self.default_register_size = None
    self.registers = None
    self.cpu = None
    self.parent = None

  def __getattr__(self, name):
    """make the register name a class attribute"""
    return self.registers[name]

  def bind_cpu(self, cpu):
    """bind a cpu to the peripheral"""
    self.cpu = cpu
    if self.registers:
      for r in self.registers.values():
        r.bind_cpu(cpu)

  def contains(self, x):
    """return True if region x is entirely within the memory space of this peripheral"""
    return (self.address <= x.adr) and ((self.address + self.size - 1) >= x.end)

  def register_list(self):
    """return an ordered register list"""
    # build a list of registers in address offset order
    # tie break with the name to give a well-defined sort order
    r_list = self.registers.values()
    r_list.sort(key=lambda x: (x.offset << 16) + sum(bytearray(x.name)))
    return r_list

  def display(self, register_name=None, fields=False):
    """return a display string for this peripheral"""
    if self.registers:
      clist = []
      if register_name is not None:
        # decode a single register
        r = self.registers[register_name]
        clist.extend(r.display(fields))
      else:
        # decode all registers
        for r in self.register_list():
          clist.extend(r.display(fields))
      return util.display_cols(clist, [0, 0, 0, 0])
    else:
      return 'no registers for %s' % self.name

  def rename_register(self, old, new):
    """rename a peripheral register old > new"""
    if old != new and old in self.registers:
      r = self.registers[old]
      del self.registers[old]
      self.registers[new] = r
      r.name = new

  def __str__(self):
    s = []
    if self.registers is not None:
      s.append('registers = {}')
      for r in self.register_list():
        s.append('%s' % r)
    s.append('p = soc.peripheral()')
    s.append('p.name = %s' % attribute_string(self.name))
    s.append('p.description = %s' % attribute_string(self.description))
    s.append('p.address = %s' % attribute_hex32(self.address))
    s.append('p.size = %s' % attribute_hex(self.size))
    s.append('p.default_register_size = %s' % self.default_register_size)
    s.append('p.registers = %s' % ('registers', 'None')[self.registers is None])
    s.append('peripherals[%s] = p\n' % attribute_string(self.name))
    return '\n'.join(s)

  def cstr(self):
    """return c code for the peripheral"""
    s = []
    s.append('// %s' % self.description)
    s.append('struct %s {' % self.name)
    s.append('};')
    s.append('')
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class cpu_info(object):
  """CPU information for the SoC"""

  def __init__(self):
    self.vendorSystickConfig = None
    self.fpuPresent = None
    self.mpuPresent = None
    self.name = None
    self.dtcmPresent = None
    self.vtorPresent = None
    self.nvicPrioBits = None
    self.fpuDP = None
    self.dcachePresent = None
    self.itcmPresent = None
    self.deviceNumInterrupts = None
    self.parent = None
    self.endian = None
    self.icachePresent = None
    self.revision = None

  def __str__(self):
    s = []
    s.append('cpu = soc.cpu_info()')
    s.append('cpu.name = %s' % attribute_string(self.name))
    s.append('cpu.revision = %s' % attribute_string(self.revision))
    s.append('cpu.endian = %s' % attribute_string(self.endian))
    s.append('cpu.mpuPresent = %s' % self.mpuPresent)
    s.append('cpu.fpuPresent = %s' % self.fpuPresent)
    s.append('cpu.fpuDP = %s' % self.fpuDP)
    s.append('cpu.icachePresent = %s' % self.icachePresent)
    s.append('cpu.dcachePresent = %s' % self.dcachePresent)
    s.append('cpu.itcmPresent = %s' % self.itcmPresent)
    s.append('cpu.dtcmPresent = %s' % self.dtcmPresent)
    s.append('cpu.vtorPresent = %s' % self.vtorPresent)
    s.append('cpu.nvicPrioBits = %s' % self.nvicPrioBits)
    s.append('cpu.vendorSystickConfig = %s' % self.vendorSystickConfig)
    s.append('cpu.deviceNumInterrupts = %s' % self.deviceNumInterrupts)
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class device(object):
  """Information for the SoC device"""

  def __init__(self):
    self.svdpath = None
    self.vendor = None
    self.name = None
    self.description = None
    self.series = None
    self.version = None
    self.cpu = None

  def __getattr__(self, name):
    """make the peripheral name a class attribute"""
    return self.peripherals[name]

  def bind_cpu(self, cpu):
    """bind a cpu to the device"""
    self.cpu = cpu
    for p in self.peripherals.values():
      p.bind_cpu(cpu)

  def insert(self, x):
    """insert a peripheral or interrupt into the device"""
    if isinstance(x, interrupt):
      assert not x.name in self.interrupts, 'device already has interrupt %s' % x.name
      x.parent = self
      self.interrupts[x.name] = x
    elif isinstance(x, peripheral):
      assert not x.name in self.peripherals, 'device already has peripheral %s' % x.name
      x.parent = self
      self.peripherals[x.name] = x

  def remove(self, p):
    """remove a peripheral from the device"""
    assert p.name in self.peripherals, 'device does not have peripheral %s' % p.name
    del self.peripherals[p.name]

  def peripheral_list(self):
    """return an ordered peripheral list"""
    # build a list of peripherals in base address order
    # base addresses for peripherals are not always unique. e.g. nordic chips
    # so tie break with the name to give a well-defined sort order
    p_list = self.peripherals.values()
    p_list.sort(key=lambda x: (x.address << 16) + sum(bytearray(x.name)))
    return p_list

  def interrupt_list(self):
    """return an ordered interrupt list"""
    # sort by irq order
    i_list = self.interrupts.values()
    i_list.sort(key=lambda x: x.irq)
    return i_list

  def cmd_map(self, ui, args):
    """display memory map"""
    clist = []
    for p in self.peripheral_list():
      start = p.address
      size = p.size
      if size is None:
        region = ': %08x' % start
      else:
        region = ': %08x %08x %s' % (start, start + size - 1, util.memsize(size))
      clist.append([p.name, region, p.description])
    ui.put('%s\n' % util.display_cols(clist, [0, 0, 0]))

  def cmd_regs(self, ui, args):
    """display peripheral registers"""
    if util.wrong_argc(ui, args, (1, 2)):
      return
    if not args[0] in self.peripherals:
      ui.put("no peripheral named '%s' (run 'map' command for the names)\n" % args[0])
      return
    p = self.peripherals[args[0]]
    if len(args) == 1:
      ui.put('%s\n' % p.display(fields=False))
      return
    if args[1] == '*':
      ui.put('%s\n' % p.display(fields=True))
      return
    if not args[1] in p.registers:
      ui.put("no register named '%s' (run 'regs %s' command for the names)\n" % (args[1], args[0]))
      return
    ui.put('%s\n' % p.display(args[1], fields=True))

  def __str__(self):
    s = []
    s.append('import soc\n')
    s.append('%s\n' % self.cpu_info)

    # dump the peripherals
    s.append('peripherals = {}')
    for p in self.peripheral_list():
      s.append('%s' % p)

    # dump the interrupts in irq order
    s.append('interrupts = {}')
    for i in self.interrupt_list():
      s.append('%s' % i)

    s.append('device = soc.device()')
    s.append('device.svdpath = %s' % attribute_string(self.svdpath))
    s.append('device.vendor = %s' % attribute_string(self.vendor))
    s.append('device.name = %s' % attribute_string(self.name))
    s.append('device.description = %s' % attribute_string(self.description))
    s.append('device.series = %s' % attribute_string(self.series))
    s.append('device.version = %s' % attribute_string(self.version))
    s.append('device.cpu_info = cpu')
    s.append('device.peripherals = peripherals')
    s.append('device.interrupts = interrupts')
    # inception!
    s.append('')
    s.append("print('%s') % device")
    return '\n'.join(s)

  def cstr(self):
    """return c code for the device"""
    s = []
    for p in self.peripheral_list():
      s.append('%s' % p.cstr())
    return '\n'.join(s)

# -----------------------------------------------------------------------------
# build a device from an svd file

def build_enumval(e, svd_e):
  if svd_e.enumeratedValue is None:
    e.enumval = None
  else:
    e.enumval = {}
    for svd_ev in svd_e.enumeratedValue:
      ev = enumval()
      ev.name = svd_ev.name
      ev.description = description_cleanup(svd_ev.description)
      ev.value = svd_ev.value
      ev.isDefault = svd_ev.isDefault
      # add it to the field
      ev.parent = e
      # store by value - that's the way we want to use it.
      e.enumval[ev.value] = ev

def build_enumvals(f, svd_f):
  """build the enumvals for a field"""
  if svd_f.enumeratedValues is None:
    f.enumvals = None
  else:
    # enumvals is a list rather than a dictionary.
    # vendors don't have to name the enumvals, so we don't have a key
    f.enumvals = []
    for svd_e in svd_f.enumeratedValues:
      e = enumvals()
      e.name = svd_e.name
      e.usage = svd_e.usage
      build_enumval(e, svd_e)
      # add it to the field
      e.parent = f
      f.enumvals.append(e)

def build_fields(r, svd_r):
  """build the fields for a register"""
  if svd_r.fields is None:
    r.fields = None
  else:
    r.fields = {}
    for svd_f in svd_r.fields:
      f = field()
      f.name = svd_f.name
      f.description = description_cleanup(svd_f.description)
      # work out the bit range
      if svd_f.bitWidth is not None:
        lsb = svd_f.bitOffset
        msb = lsb + svd_f.bitWidth - 1
      elif svd_f.msb is not None:
        lsb = svd_f.lsb
        msb = svd_f.msb
      elif svd_f.bitRange:
        (msb, lsb) = bitrange_string(svd_f.bitRange)
      else:
        assert False, 'need to work out bit field for %s' % f.name
      f.msb = msb
      f.lsb = lsb
      build_enumvals(f, svd_f)
      # add it to the register
      f.parent = r
      r.fields[f.name] = f

def build_registers(p, svd_p):
  """build the registers for a peripheral"""
  if svd_p.registers is None:
    p.registers = None
  else:
    p.registers = {}
    for svd_r in svd_p.registers:
      if svd_r.dim is None:
        r = register()
        r.name = svd_r.name
        r.description = description_cleanup(svd_r.description)
        r.size = (svd_r.size, p.default_register_size)[svd_r.size is None]
        if r.size is None:
          # still no size: default to 32 bits
          r.size = 32
        r.offset = svd_r.addressOffset
        build_fields(r, svd_r)
        # add it to the device
        r.parent = p
        p.registers[r.name] = r
      else:
        indices = build_indices(svd_r.dim, svd_r.dimIndex)
        # standard practice puts a "%s" in the name string. Is this always true?
        assert svd_r.name.__contains__('%s'), 'indexed register name %s has no %%s' % svd_r.name
        # remove the [] from the name - we want to use the name as a python variable name
        svd_name = name_cleanup(svd_r.name)
        for i in range(svd_r.dim):
          r = register()
          r.name = svd_name % indices[i]
          r.description = description_cleanup(svd_r.description)
          r.size = (svd_r.size, p.default_register_size)[svd_r.size is None]
          if r.size is None:
            # still no size: default to 32 bits
            r.size = 32
          r.offset = svd_r.addressOffset + (i * svd_r.dimIncrement)
          build_fields(r, svd_r)
          # add it to the device
          r.parent = p
          p.registers[r.name] = r

def build_peripherals(d, svd_device):
  """build the peripherals for a device"""
  d.peripherals = {}
  for svd_p in svd_device.peripherals:
    p = peripheral()
    p.name = svd_p.name
    p.description = description_cleanup(svd_p.description)
    p.address = svd_p.baseAddress
    p.size = sizeof_address_blocks(svd_p.addressBlock, 'registers')
    p.default_register_size = svd_p.size
    build_registers(p, svd_p)
    # add it to the device
    p.parent = d
    d.peripherals[p.name] = p

def build_interrupts(d, svd_device):
  """build the interrupt table for the device"""
  d.interrupts = {}
  for svd_p in svd_device.peripherals:
    if svd_p.interrupts is None:
      continue
    for svd_i in svd_p.interrupts:
      if not svd_i.name in d.interrupts:
        # add the interrupt
        i = interrupt()
        i.name = svd_i.name
        i.description = description_cleanup(svd_i.description)
        i.irq = svd_i.value
        # add it to the device
        i.parent = d
        d.interrupts[i.name] = i
      else:
        # already have this interrupt name
        # should be the same irq number
        assert d.interrupts[svd_i.name].irq == svd_i.value

def build_cpu_info(d, svd_device):
  """build the cpu info"""
  svd_cpu = svd_device.cpu
  c = cpu_info()
  c.name = svd_cpu.name
  c.revision = svd_cpu.revision
  c.endian = svd_cpu.endian
  c.mpuPresent = svd_cpu.mpuPresent
  c.fpuPresent = svd_cpu.fpuPresent
  c.fpuDP = svd_cpu.fpuDP
  c.icachePresent = svd_cpu.icachePresent
  c.dcachePresent = svd_cpu.dcachePresent
  c.itcmPresent = svd_cpu.itcmPresent
  c.dtcmPresent = svd_cpu.dtcmPresent
  c.vtorPresent = svd_cpu.vtorPresent
  c.nvicPrioBits = svd_cpu.nvicPrioBits
  c.vendorSystickConfig = svd_cpu.vendorSystickConfig
  c.deviceNumInterrupts = svd_cpu.deviceNumInterrupts
  # add it to the device
  c.parent = d
  d.cpu_info = c

def build_device(svdpath):
  """build the device structure from the svd file"""
  # read and parse the svd file
  svd_device = svd.parser(svdpath).parse()
  d = device()
  # general device information
  d.svdpath = svdpath
  d.vendor = svd_device.vendor
  d.name = svd_device.name
  d.description = description_cleanup(svd_device.description)
  d.series = svd_device.series
  d.version = svd_device.version
  # device sub components
  build_cpu_info(d, svd_device)
  build_peripherals(d, svd_device)
  build_interrupts(d, svd_device)
  return d

# -----------------------------------------------------------------------------
# make peripherals from tables

def make_enumval(parent, enum_set):
  e = {}
  for (name, value, description) in enum_set:
    ev = enumval()
    ev.name = name
    ev.description = description
    ev.value = value
    ev.parent = parent
    e[ev.value] = ev
  return e

def make_enumvals(parent, enum_set):
  if enum_set is None:
    return None
  # we build a single enumvals structure
  e = enumvals()
  e.usage = 'read'
  e.enumval = make_enumval(e, enum_set)
  e.parent = parent
  return [e,]

def make_fields(parent, field_set):
  if field_set is None:
    return None
  fields = {}
  for (name, msb, lsb, enum_set, description) in field_set:
    f = field()
    f.name = name
    f.description = description
    f.msb = msb
    f.lsb = lsb
    if callable(enum_set):
      # enum_set is actually a formatting function
      f.fmt = enum_set
    else:
      f.enumvals = make_enumvals(f, enum_set)
    f.parent = parent
    fields[f.name] = f
  return fields

def make_registers(parent, register_set):
  if register_set is None:
    return None
  registers = {}
  for (name, size, offset, field_set, description) in register_set:
    r = register()
    r.name = name
    r.description = description
    r.size = size
    r.offset = offset
    r.fields = make_fields(r, field_set)
    r.parent = parent
    registers[r.name] = r
  return registers

def make_peripheral(name, address, size, register_set, description):
  p = peripheral()
  p.name = name
  p.description = description
  p.address = address
  p.size = size
  p.registers = make_registers(p, register_set)
  return p

def make_interrupt(name, irq, description):
  i = interrupt()
  i.name = name
  i.irq = irq
  i.description = description
  return i

# -----------------------------------------------------------------------------
