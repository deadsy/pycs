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

class flash(object):

  def __init__(self, device):
    self.device = device
    self.nvmc = self.device.NVMC
    self.init = False

  def hw_init(self):
    self.init = True

#-----------------------------------------------------------------------------
