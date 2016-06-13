#-----------------------------------------------------------------------------
"""
Flash Driver for Nordic Chips

Notes:

This driver controls the pages in flash code region 1. The device I am
developing with has code region 0 unused (FICR.CLENR0 = 0xffffffff)
so this is not limitation to erasing the entire code flash.

Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.
"""
#-----------------------------------------------------------------------------

import util
import time

#-----------------------------------------------------------------------------

# NVMC.CONFIG bits
CONFIG_REN = 0 # read enable
CONFIG_WEN = 1 # write enable
CONFIG_EEN = 2 # erase enable

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, device):
    self.device = device
    self.nvmc = self.device.NVMC
    self.init = False

  def hw_init(self):
    """initialise the hardware"""
    if self.init:
      return
    self.number_of_pages = self.device.FICR.CODESIZE.rd()
    self.page_size = self.device.FICR.CODEPAGESIZE.rd()
    self.adr = self.device.flash.address
    self.size = self.number_of_pages * self.page_size
    self.init = True

  def wait4ready(self):
    """wait for flash operation completion"""
    for i in range(5):
      if self.nvmc.READY.rd() & 1:
        # operation completed
        return
      time.sleep(0.1)
    assert False, 'time out waiting for flash ready'

  def erase_page(self, adr):
    """erase a flash page"""
    self.nvmc.CONFIG.wr(CONFIG_EEN)
    self.nvmc.ERASEPAGE.wr(adr)
    self.wait4ready()
    self.nvmc.CONFIG.wr(CONFIG_REN)

  def erase(self, adr, n):
    """erase n bytes at adr"""
    self.hw_init()
    mask = ~(self.page_size - 1)
    # round down to a page boundary
    adr &= mask
    # round up to n pages
    n = (n + self.page_size - 1) & mask
    if n == 0:
      return
    n_pages = n / self.page_size

    print '%x' % adr, '%x' % n_pages

    for i in range(n_pages):
      self.erase_page(adr + (self.page_size * i))

  def __str__(self):
    self.hw_init()
    s = [
      ['flash address', ': 0x%08x' % self.adr],
      ['flash size', ': %s' % util.memsize(self.size)],
      ['page size', ': %s' % util.memsize(self.page_size)],
      ['number pages', ': %d' % self.number_of_pages],
    ]
    return util.display_cols(s)

#-----------------------------------------------------------------------------
