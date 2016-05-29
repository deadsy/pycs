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
  return "'0x%08x'" % x

# -----------------------------------------------------------------------------

class peripheral(object):

  def __init__(self, svd_peripheral):
    if svd_peripheral is None:
      return
    self.name = svd_peripheral.name
    self.description = svd_peripheral.description
    self.baseAddress = svd_peripheral.baseAddress

  def __str__(self):
    s = []
    s.append('p = soc.peripheral(None)')
    s.append('p.name = %s' % attribute_string(self.name))
    s.append('p.description = %s' % attribute_string(self.description))
    s.append('p.baseAddress = %s' % attribute_hex32(self.baseAddress))
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class cpu(object):

  def __init__(self, svd_cpu):
    # this is more or less a straight copy of the cpu info from the svd file
    if svd_cpu is None:
      return
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
    s.append('cpu = soc.cpu(None)')
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
    self.cpu = cpu(svd_device.cpu)

  def __str__(self):
    s = []
    s.append('import soc')
    s.append('%s\n' % self.cpu)
    s.append('device = soc.device()')
    s.append('device.svdpath = %s' % attribute_string(self.svdpath))
    s.append('device.vendor = %s' % attribute_string(self.vendor))
    s.append('device.name = %s' % attribute_string(self.name))
    s.append('device.description = %s' % attribute_string(self.description))
    s.append('device.series = %s' % attribute_string(self.series))
    s.append('device.version = %s' % attribute_string(self.version))
    s.append('device.cpu = cpu')
    # inception!
    s.append("print('%s') % device")
    return '\n'.join(s)

# -----------------------------------------------------------------------------
