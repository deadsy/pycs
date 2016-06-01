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
# utility functions

def description_cleanup(s):
  """cleanup a description string"""
  if s is None:
    return None
  # remove non-ascii characters
  s = s.encode('ascii', errors = 'ignore')
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
  if s is None:
    return 'None'
  # escape any ' characters
  s = s.replace("'", "\\'")
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

class interrupt(object):

  def __init__(self):
    pass

  def __str__(self):
    s = []
    s.append('i = soc.interrupt()')
    s.append('i.name = %s' % attribute_string(self.name))
    s.append('i.description = %s' % attribute_string(self.description))
    s.append('i.irq = %d' % self.irq)
    s.append('interrupts[%s] = i\n' % attribute_string(self.name))
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class field(object):

  def __init__(self):
    pass

  def __str__(self):
    s = []
    s.append('f = soc.field()')
    s.append('f.name = %s' % attribute_string(self.name))
    s.append('f.description = %s' % attribute_string(self.description))
    s.append('f.msb = %d' % self.msb)
    s.append('f.lsb = %d' % self.lsb)
    s.append('fields[%s] = f\n' % attribute_string(self.name))
    return '\n'.join(s)

# -----------------------------------------------------------------------------

class register(object):

  def __init__(self):
    pass

  def __str__(self):
    s = []
    if self.fields is not None:
      # dump the fields in most significant bit order
      s.append('fields = {}')
      f_list = self.fields.values()
      f_list.sort(key = lambda x : x.msb, reverse = True)
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

  def __init__(self):
    pass

  def __str__(self):
    s = []
    if self.registers is not None:
      s.append('registers = {}')
      # dump the registers in address offset order
      # tie break with the name to give a well-defined sort order
      r_list = self.registers.values()
      r_list.sort(key = lambda x : (x.offset << 16) + sum(bytearray(x.name)))
      for r in r_list:
        s.append('%s' % r)
    s.append('p = soc.peripheral()')
    s.append('p.name = %s' % attribute_string(self.name))
    s.append('p.description = %s' % attribute_string(self.description))
    s.append('p.address = %s' % attribute_hex32(self.address))
    s.append('p.size = %s' % attribute_hex(self.size))
    s.append('p.default_register_size = %s' % self.default_register_size)
    s.append('p.registers = registers')
    s.append('p.registers = %s' % ('registers', 'None')[self.registers is None])
    s.append('peripherals[%s] = p\n' % attribute_string(self.name))
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

    # dump the peripheral in base address order
    s.append('peripherals = {}')
    p_list = self.peripherals.values()
    p_list.sort(key = lambda x : x.address)
    for p in p_list:
      s.append('%s' % p)

    # dump the peripheral in interrupt address order
    s.append('interrupts = {}')
    i_list = self.interrupts.values()
    i_list.sort(key = lambda x : x.irq)
    for i in i_list:
      s.append('%s' % i)

    s.append('device = soc.device()')
    s.append('device.svdpath = %s' % attribute_string(self.svdpath))
    s.append('device.vendor = %s' % attribute_string(self.vendor))
    s.append('device.name = %s' % attribute_string(self.name))
    s.append('device.description = %s' % attribute_string(self.description))
    s.append('device.series = %s' % attribute_string(self.series))
    s.append('device.version = %s' % attribute_string(self.version))
    s.append('device.cpu = cpu')
    s.append('device.peripherals = peripherals')
    s.append('device.interrupts = interrupts')
    # inception!
    s.append('')
    s.append("print('%s') % device")
    return '\n'.join(s)

# -----------------------------------------------------------------------------

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
        r.size = (svd_r.size, p.size)[svd_r.size is None]
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
          r.name =  svd_name % indices[i]
          r.description = description_cleanup(svd_r.description)
          r.size = (svd_r.size, p.size)[svd_r.size is None]
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
      if not d.interrupts.has_key(svd_i.name):
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
  d.description = description_cleanup(svd_device.description)
  d.series = svd_device.series
  d.version = svd_device.version
  # device sub components
  build_cpu(d, svd_device)
  build_peripherals(d, svd_device)
  build_interrupts(d, svd_device)
  return d

# -----------------------------------------------------------------------------
