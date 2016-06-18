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

class flash(object):
  """flash driver for STM32F3xxx page based devices"""

  def __init__(self, device):
    self.device = device
    self.hw = self.device.Flash
    self.flash_main = mem.region(None, self.device.flash_main.address, self.device.flash_main.size)
    self.page_size = 2 << 10
    self.pages = []
    self.pages.extend(mem.flash_pages(self.device, 'flash_main', self.page_size))
    #self.pages.extend(mem.flash_pages(self.device, 'flash_system', self.page_size))

  def __wait4complete(self):
    """wait for flash operation completion"""
    n = 0
    while n < POLL_MAX:
      status = self.hw.SR.rd()
      if status & SR_BSY == 0:
        break
      time.sleep(POLL_TIME)
      n += 1
    # clear status bits
    self.hw.SR.wr(status | SR_EOP | SR_WRPRT | SR_PGERR)
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
    if self.hw.CR.rd() & CR_LOCK == 0:
      # already unlocked
      return
    # write the unlock sequence
    self.hw.KEYR.wr(0x45670123)
    self.hw.KEYR.wr(0xCDEF89AB)
    # clear any set CR bits
    self.hw.CR.wr(0)

  def __lock(self):
    """lock the flash"""
    self.hw.CR.set_bit(CR_LOCK)

  def __wr16(self, adr, val):
    """write 16 bits to flash"""
    # set the progam bit
    self.hw.CR.set_bit(CR_PG)
    self.device.cpu.wr(adr, val, 16)
    error = self.__wait4complete()
    # clear the progam bit
    self.hw.CR.clr_bit(CR_PG)
    return error

  def __wr_slow(self, mr, io):
    """write slow (0.69 KiB/sec) - correct"""
    for adr in xrange(mr.adr, mr.end, 2):
      self.__wr16(adr, io.rd16())

  def __wr_fast(self, mr, io):
    """write fast (6.40 KiB/sec) - muntzed"""
    self.hw.CR.wr(CR_PG)
    for adr in xrange(mr.adr, mr.end, 2):
      self.device.cpu.wr(adr, io.rd16(), 16)
    # clear the progam bit
    self.hw.CR.clr_bit(CR_PG)

  def sector_list(self):
    """return a list of flash pages"""
    return self.pages

  def check_region(self, x):
    """return None if region x meets the flash write requirements"""
    if x.adr & 1:
      return 'memory region is not 16-bit aligned'
    if x.size & 1:
      return 'memory region is not a multiple of 16-bits'
    # check that we are within flash
    if self.flash_main.contains(x):
      return None
    return 'memory region is not within flash'

  def erase_all(self):
    """erase all - return non-zero for an error"""
    # make sure the flash is not busy
    self.__wait4complete()
    # unlock the flash
    self.__unlock()
    # set the mass erase bit
    self.hw.CR.set_bit(CR_MER)
    # set the start bit
    self.hw.CR.set_bit(CR_STRT)
    # wait for completion
    error = self.__wait4complete()
    # clear the mass erase bit
    self.hw.CR.clr_bit(CR_MER)
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
    self.hw.CR.set_bit(CR_PER)
    # set the page address
    self.hw.AR.wr(page.adr)
    # set the start bit
    self.hw.CR.set_bit(CR_STRT)
    # wait for completion
    error = self.__wait4complete()
    # clear the page erase bit
    self.hw.CR.clr_bit(CR_PER)
    # lock the flash
    self.__lock()
    return (1,0)[error is None]

  def write(self, mr, io):
    """write memory region with data from an io buffer"""
    # make sure the flash is not busy
    self.__wait4complete()
    # unlock the flash
    self.__unlock()
    # write the flash
    self.__wr_fast(mr, io)
    #self.__wr_slow(mr, io)
    # lock the flash
    self.__lock()

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.pages])

#-----------------------------------------------------------------------------
