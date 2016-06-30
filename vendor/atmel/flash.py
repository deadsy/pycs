#-----------------------------------------------------------------------------
"""
Flash Driver for Atmel Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

"""
#-----------------------------------------------------------------------------

import time

import util
import mem

#-----------------------------------------------------------------------------
# Define the pages of flash memory for various devices

ATSAML21J18B_flash = (
  ('flash', (64,) * 4096),
)

# map device.soc_name to the flash map
flash_map = {
  'ATSAML21J18B': ATSAML21J18B_flash,
}

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, device):
    self.device = device
    self.hw = self.device.NVMCTRL
    self.pages = mem.flash_regions(self.device, flash_map[self.device.soc_name])

  def sector_list(self):
    """return a list of flash pages"""
    return self.pages

  def check_region(self, x):
    """return None if region x meets the flash write requirements"""
    return None

  def firmware_region(self):
    """return the name of the flash region used for firmware"""
    return 'flash'

  def erase_all(self):
    """erase all (flash and uicr) - return non-zero for an error"""
    return 0

  def erase(self, page):
    """erase a flash page - return non-zero for an error"""
    return 0

  def write(self, mr, io):
    """write memory region with data from an io buffer"""
    pass

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.pages])

#-----------------------------------------------------------------------------
