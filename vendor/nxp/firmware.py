#-----------------------------------------------------------------------------
"""

NXP Firmware Images

"""
#-----------------------------------------------------------------------------

import soc
import util

#-----------------------------------------------------------------------------
# IVT: The image vector table is a data structure in memory that tells the
# boot loader about the firmware.

def _format_IVT_tag(x):
  return ('(bad)', '(good)')[x == 0xd1]

def _format_IVT_length(x):
  return '(%d bytes)' % util.swap16(x)

def _format_IVT_version(x):
  return ('(bad)', '(good)')[x in (0x40, 0x41, 0x42, 0x43)]

_IVT_header_fieldset = (
  ('version', 31, 24, _format_IVT_version, 'version'),
  ('length', 23, 8, _format_IVT_length, 'length'),
  ('tag', 7, 0, _format_IVT_tag, 'tag'),
)

_IVT_regset = (
  ('header', 32, 0x00, _IVT_header_fieldset, 'IVT header'),
  ('entry', 32, 0x04, None, 'address of entry point'),
  ('dcd', 32, 0x0c, None, 'address of device configuration data'),
  ('boot_data', 32, 0x10, None, 'address of boot data'),
  ('this', 32, 0x14, None, 'address of IVT'),
  ('csf', 32, 0x18, None, 'address of command sequence file'),
)

#-----------------------------------------------------------------------------

class firmware:

  def __init__(self, cpu):
    self.cpu = cpu
    self.menu = (
      ('info', self.cmd_info),
    )

  def cmd_info(self, ui,args):
    """display firmware information"""
    p = soc.make_peripheral('ivt', 0x60001000, 128, _IVT_regset, 'Image Vector Table')
    p.bind_cpu(self.cpu)
    ui.put('%s\n' % p.display(fields=True))

#-----------------------------------------------------------------------------
