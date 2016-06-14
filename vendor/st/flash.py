#-----------------------------------------------------------------------------
"""
Flash Driver for ST Chips

Notes:

Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.
"""
#-----------------------------------------------------------------------------

import util

#-----------------------------------------------------------------------------

class page_based(object):
  """page based flash driver"""

  def __init__(self, device):
    self.device = device
    self.io = self.device.Flash
    self.adr = self.device.flash_main.address
    self.size = self.device.flash_main.size
    self.page_size = 2 << 10
    self.number_of_pages = self.size / self.page_size
    self.init = False

  def hw_init(self):
    """initialise the hardware"""
    if self.init:
      return
    self.init = True

  def __str__(self):
    self.hw_init()
    s = [
      ['flash address', ': 0x%08x' % self.adr],
      ['flash size', ': 0x%x (%s)' % (self.size, util.memsize(self.size))],
      ['page size', ': 0x%x (%s)' % (self.page_size, util.memsize(self.page_size))],
      ['number pages', ': %d' % self.number_of_pages],
    ]
    return util.display_cols(s)

#-----------------------------------------------------------------------------
