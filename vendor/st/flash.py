#-----------------------------------------------------------------------------
"""
Flash Driver for ST Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

2) Some ST devices talk of "flash pages" others of "flash sectors". Pages
are small and uniform in size, sectors are larger and variable in size.
No matter- this driver calls them all "sectors" and maintains a list of them.
Each page/sector is an erase unit.

"""
#-----------------------------------------------------------------------------

import util
import mem

#-----------------------------------------------------------------------------

# Flash.SR bits
SR_EOP = 1 << 5    # End of operation
SR_WRPRT = 1 << 4  # Write protection error
SR_PGERR = 1 << 2  # Programming error
SR_BSY = 1 << 0    # Busy

# Flash.CR bits
CR_FORCE_OPTLOAD = 1 << 13    # Force option byte loading
CR_EOPIE = 1 << 12            # End of operation interrupt enable
CR_ERRIE = 1 << 10            # Error interrupt enable
CR_OPTWRE = 1 << 9            # Option bytes write enable
CR_LOCK = 1 << 7              # Lock
CR_STRT = 1 << 6              # Start
CR_OPTER = 1 << 5             # Option byte erase
CR_OPTPG = 1 << 4             # Option byte programming
CR_MER = 1 << 2               # Mass erase
CR_PER = 1 << 1               # Page erase
CR_PG = 1 << 0                # Programming

#-----------------------------------------------------------------------------

def region_pages(d, name):
  """return the pages for a flash region"""
  page_size = 2 << 10
  adr = d.peripherals[name].address
  size = d.peripherals[name].size
  number_of_pages = size / page_size
  return [mem.region(name, adr + (i * page_size), page_size) for i in range(number_of_pages)]

def build_sectors(d):
  """return a list of the flash pages/sectors for this device"""
  if d.soc_name in ('STM32F303xC',):
    # page based flash
    return region_pages(d, 'flash_main') + region_pages(d, 'flash_system')
  elif d.soc_name in ('STM32F407xx',):
    # sector based flash
    return []
  else:
    assert False, 'unrecognised SoC name %s' % d.soc_name

#-----------------------------------------------------------------------------

class flash(object):
  """st flash driver"""

  def __init__(self, device):
    self.device = device
    self.io = self.device.Flash
    self.flash_sectors = build_sectors(self.device)
    self.init = False

  def __hw_init(self):
    """initialise the hardware"""
    if self.init:
      return
    self.init = True

  def __wait4busy(self):
    """wait for flash operation completion"""
    for i in xrange(5):
      # check the BSY bit
      if self.io.SR.rd() & SR_BSY == 0:
        # operation completed
        return
      time.sleep(0.1)
    assert False, 'time out waiting for not busy'

  def __unlock(self):
    """unlock the flash"""
    if self.io.CR.rd() & CR_LOCK == 0:
      # already unlocked
      return
    # write the unlock sequence
    self.io.KEYR.wr(0x45670123)
    self.io.KEYR.wr(0xCDEF89AB)

  def __lock(self):
    """lock the flash"""
    self.io.CR.wr(CR_LOCK)

  def sector_list(self):
    """return a list of flash sectors"""
    return self.flash_sectors

  def erase(self, r):
    """erase a flash region - return non-zero for an error"""
    return 0

  def erase_all(self):
    """erase all - return non-zero for an error"""
    # Check the busy bit in the FLASH_SR register
    self.__wait4busy()
    # unlock the flash
    self.__unlock()
    # Set the mass erase bit in the FLASH_CR register
    self.io.CR.wr(CR_MER)
    # Set the start bit in the FLASH_CR register
    self.io.CR.wr(CR_STRT)
    # Wait for the busy bit to be reset
    self.__wait4busy()
    # check and clear the end of programming bit
    errors = (1,0)[self.io.SR.rd() & SR_EOP != 0]
    self.io.SR.wr(0)
    # lock the flash
    self.__lock()
    return errors

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.flash_sectors])

#-----------------------------------------------------------------------------
