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

def name_lookup(l, name):
  """ lookup an item in a list by name"""
  for x in l:
    if x.name == name:
      return x
  return None

# -----------------------------------------------------------------------------

class peripheral(object):

  def __init__(self, svd_device = None, p = None):
    if svd_device is None:
      return

    if p.derived_from is None:
      p_from = p
      self.df_name = None
    else:
      p_from = p.derived_from
      self.df_name = p_from.name

    self.name = p.name
    self.description = p_from.description
    self.baseAddress = p.baseAddress
    self.size = svd.sizeof_address_blocks(p_from.addressBlock, 'registers')
    self.registers = []

  def __str__(self):
    s = []
    if self.df_name is not None:
      s.append("registers = soc.name_lookup(peripherals, '%s').registers" % self.df_name)
    else:
      s.append('registers = []')
      for r in self.registers:
        s.append('%s' % r)
        s.append('registers.append(r)\n')

    s.append('p = soc.peripheral()')
    s.append('p.name = %s' % attribute_string(self.name))
    s.append('p.df_name = %s' % attribute_string(self.df_name))
    s.append('p.description = %s' % attribute_string(self.description))
    s.append('p.baseAddress = %s' % attribute_hex32(self.baseAddress))
    s.append('p.size = %s' % attribute_hex(self.size))
    s.append('p.registers = registers')
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
        self.peripherals.append(peripheral(svd_device, p))
    # derived peripherals
    for p in svd_device.peripherals:
      if p.derived_from:
        self.peripherals.append(peripheral(svd_device, p))

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
    s.append("print('%s') % device")
    return '\n'.join(s)

# -----------------------------------------------------------------------------
