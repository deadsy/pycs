#-----------------------------------------------------------------------------
"""
Flash Driver for ST Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

2) Some ST devices talk of "flash pages" others of "flash sectors". Pages
are small and uniform in size, sectors are larger and variable in size.
No matter- this driver calls them all "sectors" and maintains a list of them.
Each sector is an erase unit.

"""
#-----------------------------------------------------------------------------

import util
import mem

#-----------------------------------------------------------------------------

def page_based_flash(d):
  """return a list of the flash pages for this device"""
  pages = []
  page_size = 2 << 10

  # flash_main
  adr = d.flash_main.address
  size = d.flash_main.size
  number_of_pages = size / page_size
  for i in range(number_of_pages):
    pages.append(mem.region('flash_main', adr + (i * page_size), page_size))

  # flash_system
  adr = d.flash_system.address
  size = d.flash_system.size
  number_of_pages = size / page_size
  for i in range(number_of_pages):
    pages.append(mem.region('flash_system', adr + (i * page_size), page_size))

  return pages

def sector_based_flash(d):
  """return a list of the sectors for the flash on this device"""
  return []

#-----------------------------------------------------------------------------

class flash(object):
  """st flash driver"""

  def __init__(self, device):
    self.device = device
    self.io = self.device.Flash
    self.init = False

  def __hw_init(self):
    """initialise the hardware"""
    if self.init:
      return
    self.init = True

  def sector_list(self):
    """return a list of flash sectors"""
    return self.device.flash_sectors

  def erase(self, r):
    """erase a flash region - return non-zero for an error"""
    self.__hw_init()
    return 0

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.flash_sectors])

#-----------------------------------------------------------------------------
