#-----------------------------------------------------------------------------
"""
Flash Driver for Nordic Chips

Notes:

Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.
"""
#-----------------------------------------------------------------------------

import time

import util
import mem

#-----------------------------------------------------------------------------

# NVMC.CONFIG bits
CONFIG_REN = 0 # read enable
CONFIG_WEN = 1 # write enable
CONFIG_EEN = 2 # erase enable

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, device):
    self.device = device
    self.io = self.device.NVMC
    self.init = False

  def __hw_init(self):
    """initialise the hardware"""
    if self.init:
      return
    self.number_of_pages = self.device.FICR.CODESIZE.rd()
    self.page_size = self.device.FICR.CODEPAGESIZE.rd()
    self.adr = self.device.flash1.address
    self.size = self.number_of_pages * self.page_size
    self.init = True

  def __wait4ready(self):
    """wait for flash operation completion"""
    for i in xrange(5):
      if self.io.READY.rd() & 1:
        # operation completed
        return
      time.sleep(0.1)
    assert False, 'time out waiting for flash ready'

  def region_list(self):
    """return a list of erase regions"""
    self.__hw_init()
    # for this device the page is the erase unit
    return [mem.region(self.adr + (i * self.page_size), self.page_size) for i in range(self.number_of_pages)]

  def erase(self, p):
    """erase a flash page - return non-zero for an error"""
    self.__hw_init()
    self.io.CONFIG.wr(CONFIG_EEN)
    self.io.ERASEPAGE.wr(p.adr)
    self.__wait4ready()
    self.io.CONFIG.wr(CONFIG_REN)
    return 0

  def __str__(self):
    self.__hw_init()
    s = [
      ['flash address', ': 0x%08x' % self.adr],
      ['flash size', ': 0x%x (%s)' % (self.size, util.memsize(self.size))],
      ['page size', ': 0x%x (%s)' % (self.page_size, util.memsize(self.page_size))],
      ['number pages', ': %d' % self.number_of_pages],
    ]
    return util.display_cols(s)

#-----------------------------------------------------------------------------
