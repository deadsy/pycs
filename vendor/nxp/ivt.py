#-----------------------------------------------------------------------------
"""

IVT Image Vector Table

The image vector table is a data structure in memory that tells the boot
loader about the firmware.

"""
#-----------------------------------------------------------------------------

import struct

#-----------------------------------------------------------------------------

_tag = 0xd1
_length = 0x20

class ivt:
  """Image Vector Table"""

  def __init__(self):
    self.header = 0
    self.entry = 0
    self.dcd = 0
    self.boot_data = 0
    self.this = 0
    self.csf = 0

  def read(self, data):
    """parse a buffer of ivt data"""
    if len(data) >= _length:
      return 'too short'
    x = struct.unpack('LLLLLLLL', data)
    self.header = x[0]
    self.entry = x[1]
    self.dcd = x[3]
    self.boot_data = x[4]
    self.this = x[5]
    self.csf = x[6]
    if (self.header >> 24) != _tag:
      return 'invalid header tag'
    if ((self.header >> 8) & 0xffff) != _length:
      return 'bad header length'
    if (self.header & 0xff) not in (0x40, 0x41, 0x42, 0x43):
      return 'bad header version'
    return None

  def __str__(self):
    s = []
    s.append('header %08x' % self.header)
    s.append('entry %08x' % self.entry)
    s.append('dcd %08x' % self.dcd)
    s.append('boot_data %08x' % self.boot_data)
    s.append('self %08x' % self.this)
    s.append('csf %08x' % self.csf)
    return ''.join(s)

#-----------------------------------------------------------------------------
