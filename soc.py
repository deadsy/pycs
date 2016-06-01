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

class field(object):

  def __init__(self):
    pass

# -----------------------------------------------------------------------------

class register(object):

  def __init__(self):
    pass

# -----------------------------------------------------------------------------

class peripheral(object):

  def __init__(self):
    pass

  def __str__(self):
    s = []
#    # registers
#    if self.df_name is None:
#      s.append('registers = []')
#      for r in self.registers:
#        s.append('%s' % r)
#        s.append('registers.append(r)')

    s.append('p = soc.peripheral()')
    s.append('p.name = %s' % attribute_string(self.name))
    s.append('p.baseAddress = %s' % attribute_hex32(self.baseAddress))
    s.append('p.size = %s' % attribute_hex(self.size))
    s.append('p.description = %s' % attribute_string(self.description))
    return '\n'.join(s)


# -----------------------------------------------------------------------------

class cpu(object):

  def __init__(self):
    pass

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

  def __str__(self):
    s = []
    s.append('import soc\n')
    s.append('%s\n' % self.cpu)

    s.append('peripherals = {}')
    for (name, p) in self.peripherals.items():
      s.append('%s' % p)
      s.append('peripherals[%s] = p\n' % attribute_string(name))

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

def build_peripherals(d, svd_device):
  """build the peripherals"""
  d.peripherals = {}
  for svd_p in svd_device.peripherals:
    p = peripheral()
    p.name = svd_p.name
    p.baseAddress = svd_p.baseAddress
    p.size = svd_p.size

    print('looking for description of %s' % p.name)
    p.description = svd_p.description
    print('done')

    # add it to the device
    p.parent = d
    d.peripherals[p.name] = p

def build_cpu(d, svd_device):
  """build the cpu"""
  svd_cpu = svd_device.cpu
  c = cpu()
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
  d.cpu = c

def build_device(svdpath):
  """build the device structure from the svd file"""
  # read and parse the svd file
  svd_device = svd.parser(svdpath).parse()
  d = device()
  # general device information
  d.svdpath = svdpath
  d.vendor = svd_device.vendor
  d.name = svd_device.name
  d.description = svd_device.description
  d.series = svd_device.series
  d.version = svd_device.version
  # device sub components
  build_cpu(d, svd_device)
  build_peripherals(d, svd_device)
  return d

# -----------------------------------------------------------------------------
