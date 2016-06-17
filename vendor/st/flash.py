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

import time
import util
import mem

#-----------------------------------------------------------------------------

POLL_MAX = 5
POLL_TIME = 0.1

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

#-----------------------------------------------------------------------------

class flash(object):
  """flash driver for STM32F3xxx page based devices"""

  def __init__(self, device):
    self.device = device
    self.io = self.device.Flash
    self.flash_main = mem.region(None, self.device.flash_main.address, self.device.flash_main.size)
    self.pages = region_pages(self.device, 'flash_main') #  + region_pages(d, 'flash_system')

  def __wait4complete(self):
    """wait for flash operation completion"""
    n = 0
    while n < POLL_MAX:
      status = self.io.SR.rd()
      if status & SR_BSY == 0:
        break
      time.sleep(POLL_TIME)
      n += 1
    # clear status bits
    self.io.SR.wr(status | SR_EOP | SR_WRPRT | SR_PGERR)
    # check for errors
    if n >= POLL_MAX:
      return 'timeout'
    if status & SR_WRPRT:
      return 'write protect error'
    if status & SR_PGERR:
      return 'programming error'
    # done
    return None

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
    self.io.CR.set_bit(CR_LOCK)

  def __wr16(self, adr, val):
    """write 16 bits to flash"""
    # set the progam bit
    self.io.CR.set_bit(CR_PG)
    self.device.cpu.wr(adr, val, 16)
    errors = self.__wait4complete()
    # clear the progam bit
    self.io.CR.clr_bit(CR_PG)
    return errors

  def sector_list(self):
    """return a list of flash pages"""
    return self.pages

  def in_flash(self, x):
    """return True if x is contained within a flash region"""
    if self.flash_main.contains(x):
      return True
    return False

  def erase_all(self):
    """erase all - return non-zero for an error"""
    # make sure the flash is not busy
    self.__wait4complete()
    # unlock the flash
    self.__unlock()
    # set the mass erase bit
    self.io.CR.set_bit(CR_MER)
    # set the start bit
    self.io.CR.set_bit(CR_STRT)
    # wait for completion
    error = self.__wait4complete()
    # clear the mass erase bit
    self.io.CR.clr_bit(CR_MER)
    # lock the flash
    self.__lock()
    return (1,0)[error is None]

  def erase(self, page):
    """erase a flash page - return non-zero for an error"""
    # make sure the flash is not busy
    self.__wait4complete()
    # unlock the flash
    self.__unlock()
    # set the page erase bit
    self.io.CR.set_bit(CR_PER)
    # set the page address
    self.io.AR.wr(page.adr)
    # set the start bit
    self.io.CR.set_bit(CR_STRT)
    # wait for completion
    error = self.__wait4complete()
    # clear the page erase bit
    self.io.CR.clr_bit(CR_PER)
    # lock the flash
    self.__lock()
    return (1,0)[error is None]

  def write(self, r, io):
    """write memory region r with the data from the io buffer"""
    # make sure the flash is not busy
    self.__wait4complete()
    # unlock the flash
    self.__unlock()

    self.__wr16(2, 0xbabe)

    # lock the flash
    self.__lock()

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.pages])

#-----------------------------------------------------------------------------
