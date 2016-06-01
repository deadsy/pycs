# -----------------------------------------------------------------------------
"""

SoC Object

Takes an SVD file, parses it, and then re-expresses it as a python object
that matches the requirements of pycs. Typically the resulting data structures
will need some vendor/device specific tweaking to make up for things in the svd
file that are missing or wrong. These tweaks are done by the vendor specific SoC
code.

Note: The str() functions are setup so printing the structures will produce
*.py code to represent the structures. This is useful for debugging svd contents.

"""
# -----------------------------------------------------------------------------

import svd

# -----------------------------------------------------------------------------

def attribute_string(s):
  if s is None:
    return 'None'
  return "'%s'" % s

def attribute_hex32(x):
  if x is None:
    return 'None'
  return '0x%08x' % x

def attribute_hex(x):
  if x is None:
    return 'None'
  return '0x%x' % x

# -----------------------------------------------------------------------------

def lookup(l, name):
  """ lookup an item in a list by name"""
  for x in l:
    if x.name == name:
      return x
  return None

# -----------------------------------------------------------------------------

class register(object):

  def __init__(self, r = None, df_r = None, size = None):
    """initialise a derived or non-derived register"""
    if r is None:
      return
    self.name = r.name
    if df_r is None:
      # non-derived register
      self.df_name = None
      # get the default size from the peripheral if the register has no size
      self.size = (r.size, size)[r.size is None]
      if self.size is None:
        # still no size: default to 32 bits
        self.size = 32
    else:
      # derived register
      self.df_name = df_r.name
      self.size = df_r.size

  def __str__(self):
    s = []
    # register
    s.append('r = soc.register()')
    s.append('r.name = %s' % attribute_string(self.name))
    s.append('r.df_name = %s' % attribute_string(self.df_name))
    if self.df_name is None:
      s.append('r.size = %d' % self.size)
    else:
      s.append('r.size = soc.lookup(registers, r.df_name).size')
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class peripheral(object):

  def __init__(self, p = None, df_p = None):
    """initialise a derived or non-derived peripheral"""
    if p is None:
      return
    self.name = p.name
    self.baseAddress = p.baseAddress
    if df_p is None:
      # non-derived peripheral
      self.df_name = None
      self.description = p.description
      self.size = svd.sizeof_address_blocks(p.addressBlock, 'registers')
      self.build_registers(p)
    else:
      # derived peripheral
      self.df_name = df_p.name
      self.description = df_p.description
      self.size = df_p.size
      self.registers = df_p.registers

  def build_registers(self, p):
    """build the registers list"""
    self.registers = []

    # non-derived registers
    for r in p.registers:
      if r.derived_from is None:
        self.registers.append(register(r, size = p.size))
    # derived registers
    for r in p.registers:
      if r.derived_from:
        df_r = lookup(self.registers, r.derived_from.name)
        self.registers.append(register(r, df_r))

  def __str__(self):
    s = []
    # registers
    if self.df_name is None:
      s.append('registers = []')
      for r in self.registers:
        s.append('%s' % r)
        s.append('registers.append(r)')
    # peripheral
    s.append('p = soc.peripheral()')
    s.append('p.name = %s' % attribute_string(self.name))
    s.append('p.df_name = %s' % attribute_string(self.df_name))
    s.append('p.baseAddress = %s' % attribute_hex32(self.baseAddress))
    s.append('p.size = %s' % attribute_hex(self.size))
    if self.df_name is None:
      s.append('p.description = %s' % attribute_string(self.description))
      s.append('p.registers = registers')
    else:
      s.append('p.description = soc.lookup(peripherals, p.df_name).description')
      s.append('p.registers = soc.lookup(peripherals, p.df_name).registers')
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class cpu(object):

  def __init__(self, svd_device = None):
    # this is more or less a straight copy of the cpu info from the svd file
    if svd_device is None:
      return
    svd_cpu = svd_device.cpu
    self.name = svd_cpu.name
    self.revision = svd_cpu.revision
    self.endian = svd_cpu.endian
    self.mpuPresent = svd_cpu.mpuPresent
    self.fpuPresent = svd_cpu.fpuPresent
    self.fpuDP = svd_cpu.fpuDP
    self.icachePresent = svd_cpu.icachePresent
    self.dcachePresent = svd_cpu.dcachePresent
    self.itcmPresent = svd_cpu.itcmPresent
    self.dtcmPresent = svd_cpu.dtcmPresent
    self.vtorPresent = svd_cpu.vtorPresent
    self.nvicPrioBits = svd_cpu.nvicPrioBits
    self.vendorSystickConfig = svd_cpu.vendorSystickConfig
    self.deviceNumInterrupts = svd_cpu.deviceNumInterrupts

  def __str__(self):
    s = []
    s.append('cpu = soc.cpu()')
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

  def __init__(self):
    pass

  def build_peripherals(self, svd_device):
    """build the peripherals list"""
    self.peripherals = []
    # non-derived peripherals
    for p in svd_device.peripherals:
      if p.derived_from is None:
        self.peripherals.append(peripheral(p))
    # derived peripherals
    for p in svd_device.peripherals:
      if p.derived_from:
        df_p = lookup(self.peripherals, p.derived_from.name)
        self.peripherals.append(peripheral(p, df_p))

  def read_svd(self, svdpath):
    self.svdpath = svdpath
    svd_device = svd.parser(self.svdpath).parse()
    # general device information
    self.vendor = svd_device.vendor
    self.name = svd_device.name
    self.description = svd_device.description
    self.series = svd_device.series
    self.version = svd_device.version
    # cpu information
    self.cpu = cpu(svd_device)
    # peripherals
    self.build_peripherals(svd_device)

  def __str__(self):
    s = []
    s.append('import soc\n')
    s.append('%s\n' % self.cpu)

    s.append('peripherals = []')
    for p in self.peripherals:
      s.append('%s' % p)
      s.append('peripherals.append(p)\n')

    s.append('device = soc.device()')
    s.append('device.svdpath = %s' % attribute_string(self.svdpath))
    s.append('device.vendor = %s' % attribute_string(self.vendor))
    s.append('device.name = %s' % attribute_string(self.name))
    s.append('device.description = %s' % attribute_string(self.description))
    s.append('device.series = %s' % attribute_string(self.series))
    s.append('device.version = %s' % attribute_string(self.version))
    s.append('device.cpu = cpu')
    s.append('device.peripherals = peripherals')
    # inception!
    s.append('')
    s.append("print('%s') % device")
    return '\n'.join(s)

# -----------------------------------------------------------------------------
