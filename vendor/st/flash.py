#-----------------------------------------------------------------------------
"""
Flash Driver for ST Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

2) Some ST devices talk of "flash pages" others of "flash sectors". Pages
are small and uniform in size, sectors are larger and variable in size.
There are two drivers here: one for page based flash, the other the other for
sector based flash. Each page/sector is an erase unit.

"""
#-----------------------------------------------------------------------------

import time
import util
import mem

#-----------------------------------------------------------------------------
# Define the sectors/pages of flash memory for various devices

# STM32F40x/STM32F41x
STM32F40x_flash = (
  ('flash_main', (16<<10,16<<10,16<<10,16<<10,64<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10), range(12)),
  ('flash_system', (30<<10,)),
  ('flash_otp', (528,)),
  ('flash_option', (16,)),
)

#STM32F303xD/E: Up to 512KiB
#STM32F303x6/8, STM32F328x8: up to 64 KiB

#STM32F303xB/C, STM32F358xC: up to 256 KiB
STM32F303xC_flash = (
  ('flash_main', (2<<10,) * 128),
  ('flash_system', (2<<10,) * 4),
  ('flash_option', (16,)),
)

# map device.soc_name to the flash map
flash_map = {
  'STM32F303xC': STM32F303xC_flash,
  'STM32F407xx': STM32F40x_flash,
}

#-----------------------------------------------------------------------------

POLL_MAX = 5
POLL_TIME = 0.1

#-----------------------------------------------------------------------------

class pdrv(object):
  """flash driver for STM32F3xxx page based devices"""

  # Flash.SR bits
  SR_EOP = 1 << 5    # End of operation
  SR_WRPRT = 1 << 4  # Write protection error
  SR_PGERR = 1 << 2  # Programming error
  SR_BSY = 1 << 0    # Busy

  # Flash.CR bits
  CR_FORCE_OPTLOAD = 1 << 13 # Force option byte loading
  CR_EOPIE = 1 << 12         # End of operation interrupt enable
  CR_ERRIE = 1 << 10         # Error interrupt enable
  CR_OPTWRE = 1 << 9         # Option bytes write enable
  CR_LOCK = 1 << 7           # Lock
  CR_STRT = 1 << 6           # Start
  CR_OPTER = 1 << 5          # Option byte erase
  CR_OPTPG = 1 << 4          # Option byte programming
  CR_MER = 1 << 2            # Mass erase
  CR_PER = 1 << 1            # Page erase
  CR_PG = 1 << 0             # Programming

  def __init__(self, device):
    self.device = device
    self.hw = self.device.Flash
    self.pages = mem.flash_regions(self.device, flash_map[self.device.soc_name])

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
      val = io.rd16()
      if val != 0xffff:
        self.__wr16(adr, val)

  def __wr_fast(self, mr, io):
    """write fast (6.40 KiB/sec) - muntzed"""
    # set the progam bit
    self.hw.CR.wr(CR_PG)
    for adr in xrange(mr.adr, mr.end, 2):
      val = io.rd16()
      if val != 0xffff:
        self.device.cpu.wr(adr, val, 16)
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
    if self.device.flash_main.contains(x):
      return None
    return 'memory region is not within flash'

  def firmware_region(self):
    """return the name of the flash region used for firmware"""
    return 'flash_main'

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

class sdrv(object):
  """flash driver for STM32F3xxx sector based devices"""

  # FLASH.SR bits
  SR_BSY    = 1 << 16 # Busy
  SR_RDERR  = 1 << 8  # Read error
  SR_PGSERR = 1 << 7  # Programming sequence error
  SR_PGPERR = 1 << 6  # Programming parallelism error
  SR_PGAERR = 1 << 5  # Programming alignment error
  SR_WRPERR = 1 << 4  # Write protection error
  SR_OPERR  = 1 << 1  # Operation error
  SR_EOP    = 1 << 0  # End of operation

  # FLASH.CR bits
  CR_LOCK   = 1 << 31 # Lock
  CR_ERRIE  = 1 << 25 # Error interrupt enable
  CR_EOPIE  = 1 << 24 # End of operation interrupt enable
  CR_STRT   = 1 << 16 # Start
  CR_MER1   = 1 << 15 # Mass Erase (bank2)
  #CR_SNB[7:3]      : 0                             Sector number
  CR_MER    = 1 << 2  # Mass Erase (bank1)
  CR_SER    = 1 << 1  # Sector Erase
  CR_PG     = 1 << 0  # Programming
  # FLASH.CR.CR_PSIZE voltage ranges
  VOLTS_18_21     = 0 << 8 # 1.8V to 2.1V
  VOLTS_21_27     = 1 << 8 # 2.1V to 2.7V
  VOLTS_27_36     = 2 << 8 # 2.7V to 3.6V
  VOLTS_27_36_VPP = 3 << 8 # 2.7V to 3.6V + External Vpp
  # FLASH.CR.CR_PSIZE write size
  PSIZE_BYTE        = 0 << 8 # 8 bits
  PSIZE_HALF_WORD   = 1 << 8 # 16 bits
  PSIZE_WORD        = 2 << 8 # 32 bits
  PSIZE_DOUBLE_WORD = 3 << 8 # 64 bits

  def __init__(self, device):
    self.device = device
    self.hw = self.device.FLASH
    self.sectors = mem.flash_regions(self.device, flash_map[self.device.soc_name])
    # set an overall voltage to control the erase/write parrallelism
    self.volts = self.VOLTS_27_36

  def __wait4complete(self, timeout = POLL_MAX):
    """wait for flash operation completion"""
    n = 0
    while n < timeout:
      status = self.hw.SR.rd()
      if status & self.SR_BSY == 0:
        break
      time.sleep(POLL_TIME)
      n += 1
    # clear status bits
    clr = self.SR_RDERR | self.SR_PGSERR | self.SR_PGPERR | self.SR_PGAERR | self.SR_WRPERR | self.SR_OPERR | self.SR_EOP
    self.hw.SR.wr(clr)
    # check for errors
    if n >= timeout:
      return 'timeout'
    if status & self.SR_RDERR:
      return 'read error'
    if status & self.SR_PGSERR:
      return 'program sequence error'
    if status & self.SR_PGPERR:
      return 'program parallelism error'
    if status & self.SR_PGAERR:
      return 'program alignment error'
    if status & self.SR_WRPERR:
      return 'write protect error'
    if status & self.SR_OPERR:
      return 'operation error'
    # done
    return None

  def __unlock(self):
    """unlock the flash"""
    if self.hw.CR.rd() & self.CR_LOCK == 0:
      # already unlocked
      return
    # write the unlock sequence
    self.hw.KEYR.wr(0x45670123)
    self.hw.KEYR.wr(0xCDEF89AB)
    # clear any set CR bits
    self.hw.CR.wr(0)

  def __lock(self):
    """lock the flash"""
    self.hw.CR.set_bit(self.CR_LOCK)

  def __mass_erase(self, banks = 1):
    """setup CR for the mass erase"""
    # set the parallelism based on voltage range
    cr = self.volts
    # set the banks to erase
    if banks & 1:
      cr |= self.CR_MER
    if banks & 2:
      cr |= self.CR_MER1
    self.hw.CR.wr(cr)

  def __sector_erase(self, sector):
    """setup CR for the sector erase"""
    cr = self.CR_SER | self.volts
    # Need to add offset of 4 when sector higher than 11
    if sector > 11:
      sector += 4
    cr |= sector << 3
    self.hw.CR.wr(cr)

  def __wr32(self, adr, val):
    """write 32 bits to flash"""
    # set the progam bit and write size
    self.hw.CR.wr(self.CR_PG | self.PSIZE_WORD)
    self.device.cpu.wr(adr, val, 32)
    error = self.__wait4complete()
    # clear the progam bit
    self.hw.CR.clr_bit(self.CR_PG)
    return error

  def __wr_slow(self, mr, io):
    """write slow (1.95 KiB/sec) - correct"""
    for adr in xrange(mr.adr, mr.end, 4):
      val = io.rd32()
      if val != 0xffffffff:
        self.__wr32(adr, val)

  def __wr_fast(self, mr, io):
    """write fast (11.89 KiB/sec) - muntzed"""
    # set the progam bit and write size
    self.hw.CR.wr(self.CR_PG | self.PSIZE_WORD)
    for adr in xrange(mr.adr, mr.end, 4):
      val = io.rd32()
      if val != 0xffffffff:
        self.device.cpu.wr(adr, val, 32)
    # clear the progam bit
    self.hw.CR.clr_bit(self.CR_PG)

  def sector_list(self):
    """return a list of flash sectors"""
    return self.sectors

  def check_region(self, x):
    """return None if region x meets the flash write requirements"""
    if x.adr & 3:
      return 'memory region is not 32-bit aligned'
    if x.size & 3:
      return 'memory region is not a multiple of 32-bits'
    # check that we are within flash
    if self.device.flash_main.contains(x):
      return None
    return 'memory region is not within flash'

  def firmware_region(self):
    """return the name of the flash region used for firmware"""
    return 'flash_main'

  def erase_all(self):
    """erase all - return non-zero for an error"""
    # make sure the flash is not busy
    self.__wait4complete()
    # unlock the flash
    self.__unlock()
    # setup the mass erase
    self.__mass_erase()
    # set the start bit
    self.hw.CR.set_bit(self.CR_STRT)
    # wait for completion
    error = self.__wait4complete(100)
    # clear any set CR bits
    self.hw.CR.wr(0)
    # lock the flash
    self.__lock()
    return (1,0)[error is None]

  def erase(self, sector):
    """erase a flash sector - return non-zero for an error"""
    pass

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
    return util.display_cols([x.col_str() for x in self.sectors])

#-----------------------------------------------------------------------------
