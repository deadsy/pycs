#-----------------------------------------------------------------------------
"""
Flash Driver for ST Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

2) The ST device families have similar and yet different flash controller hardware.
Each family get's it's own driver class to deal with the differences.

3) You can write the flash directly from Python code, but it is slow. The fast
approach is to load the data and a flash programming routine into RAM and run it directly
on the target CPU. This minimises debugger IO transactions.

"""
#-----------------------------------------------------------------------------

import time
import util
import mem
import vendor.st.lib as lib

#-----------------------------------------------------------------------------
# Define the sectors/pages of flash memory for various devices

class meta(object):
  """bank and sector numbering"""

  def __init__(self, sector, bank = None):
    self.sector = sector
    self.bank = bank

  def __str__(self):
    if self.bank is None:
      return 'sector%d' % self.sector
    elif self.sector is None:
      return 'bank%d' % self.bank
    else:
      return 'bank%d sector%d' % (self.bank, self.sector)

class page(object):
  """page and bank numbering"""

  def __init__(self, page, bank = None):
    self.page = page
    self.bank = bank

  def __str__(self):
    if self.bank is None:
      return 'page %d' % self.page
    elif self.page is None:
      return 'bank %d' % self.bank
    else:
      return 'bank %d page %d' % (self.bank, self.page)

# STM32F40x/STM32F41x
STM32F40x_flash = (
  ('flash_main', (16<<10,16<<10,16<<10,16<<10,64<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10),
    (meta(0), meta(1),meta(2),meta(3),meta(4),meta(5),meta(6),meta(7),meta(8),meta(9),meta(10),meta(11))),
  ('flash_system', (30<<10,)),
  ('flash_otp', (528,)),
  ('flash_option', (16,)),
)

# STM32F42xxx

STM32F429xI_flash = (
  ('flash_main', (16<<10,16<<10,16<<10,16<<10,64<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10,
                  16<<10,16<<10,16<<10,16<<10,64<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10),
                 (meta(0,1),meta(1,1),meta(2,1),meta(3,1),meta(4,1),meta(5,1),meta(6,1),meta(7,1),meta(8,1),meta(9,1),meta(10,1),meta(11,1),
                  meta(12,2),meta(13,2),meta(14,2),meta(15,2),meta(16,2),meta(17,2),meta(18,2),meta(19,2),meta(20,2),meta(21,2),meta(22,2),meta(23,2))),
  ('flash_system', (30<<10,) * 1),
  ('flash_otp', (528,)),
  ('flash_opt_bank1', (16,),(meta(None,1),)),
  ('flash_opt_bank2', (16,),(meta(None,2),)),
)

STM32F427xG_flash = (
  ('flash_main', (16<<10,16<<10,16<<10,16<<10,64<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10,128<<10),
                 (meta(0,1),meta(1,1),meta(2,1),meta(3,1),meta(4,1),meta(5,1),meta(6,1),meta(7,1),meta(8,1),meta(9,1),meta(10,1),meta(11,1))),
  ('flash_system', (30<<10,) * 1),
  ('flash_otp', (528,)),
  ('flash_opt_bank1', (16,),(meta(None,1),)),
  ('flash_opt_bank2', (16,),(meta(None,2),)),
)

#STM32F303xD/E: Up to 512KiB
#STM32F303x6/8, STM32F328x8: up to 64 KiB

#STM32F303xB/C, STM32F358xC: up to 256 KiB
STM32F303xC_flash = (
  ('flash_main', (2<<10,) * 128),
  ('flash_system', (2<<10,) * 4),
  ('flash_option', (16,)),
)

STM32L432KC_flash = (
  ('flash_main', (2 << 10,) * 128, tuple([page(i) for i in range(128)])),
  ('flash_system', (28 << 10,)),
  ('flash_otp', (1 << 10,)),
  ('flash_option', (16,)),
)

STM32F091xC_flash = (
  ('flash_main', (2 << 10,) * 128, tuple([page(i) for i in range(128)])),
  ('flash_system', (8 << 10,)),
  ('flash_option', (16,)),
)

# map device.soc_name to the flash map
flash_map = {
  'STM32F303xC': STM32F303xC_flash,
  'STM32F407xx': STM32F40x_flash,
  'STM32F427xG': STM32F427xG_flash,
  'STM32F429xI': STM32F429xI_flash,
  'STM32L432KC': STM32L432KC_flash,
  'STM32F091xC': STM32F091xC_flash,
}

#-----------------------------------------------------------------------------

POLL_MAX = 5
POLL_TIME = 0.1

#-----------------------------------------------------------------------------

class flash(object):
  """common flash driver functions"""

  def wait4complete(self):
    """wait for flash operation completion"""
    n = 0
    while n < POLL_MAX:
      status = self.hw.SR.rd()
      if status & self.SR_BSY == 0:
        break
      time.sleep(POLL_TIME)
      n += 1
    # clear status bits
    self.hw.SR.wr(status | self.SR_EOP | self.SR_errors)
    # check for errors
    if n >= POLL_MAX:
      return 'timeout'
    return self.check_errors(status)

  def unlock(self):
    """unlock the flash"""
    if self.hw.CR.rd() & self.CR_LOCK == 0:
      # already unlocked
      return
    # write the unlock sequence
    self.hw.KEYR.wr(0x45670123)
    self.hw.KEYR.wr(0xCDEF89AB)
    # clear any set CR bits
    self.hw.CR.wr(0)

  def lock(self):
    """lock the flash"""
    self.hw.CR.set_bit(self.CR_LOCK)

  def wr_lib(self, mr, io):
    """write to flash using asm library code"""
    # load the library
    self.device.cpu.loadlib(self.lib)
    words_to_write = mr.size / 4
    words_per_buf = self.device.rambuf.size / 4
    src = self.device.rambuf.adr
    dst = mr.adr
    while words_to_write > 0:
      # program a full buffer, or whatever is left
      n = min(words_to_write, words_per_buf)
      # copy the io buffer to the ram buffer
      self.device.cpu.wrmem32(src, n, io)
      # setup the registers and call the library
      self.device.cpu.wrreg('r0', src)
      self.device.cpu.wrreg('r1', dst)
      self.device.cpu.wrreg('r2', n)
      status = self.device.cpu.runlib(self.lib)
      # check for errors
      err = self.check_errors(status)
      if err:
        return err
      # next buffer
      words_to_write -= n
      dst += 4 * n
    return None

  # Public API

  def write(self, mr, io):
    """write memory region with data from an io buffer"""
    # halt the cpu- don't try to run while we change flash
    self.device.cpu.halt()
    # make sure the flash is not busy
    self.wait4complete()
    # unlock the flash
    self.unlock()
    # write the flash
    self.wr_lib(mr, io)
    # lock the flash
    self.lock()

#-----------------------------------------------------------------------------

class stm32f0xx(flash):
  """flash driver for STM32F0xx, STM32F3xxx devices"""

  # FLASH.SR bits
  SR_EOP = 1 << 5   # End of operation
  SR_WRPRT = 1 << 4 # Write protection error
  SR_PGERR = 1 << 2 # Programming error
  SR_BSY = 1 << 0   # Busy

  SR_errors = (SR_WRPRT|SR_PGERR)

  # FLASH.CR bits
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
    self.lib = lib.stm32f0xx_flash

  def check_errors(self, status):
    """check the error bits in the status value"""
    if status & self.SR_WRPRT:
      return 'write protect error'
    elif status & self.SR_PGERR:
      return 'programming error'
    return None

  # Public API

  def sector_list(self):
    """return a list of flash pages"""
    return self.pages

  def check_region(self, x):
    """return None if region x meets the flash write requirements"""
    # Flash writing on this chip is 16-bits at a time with 16 bit alignment.
    if x.adr & 1:
      return 'memory region is not 16-bit aligned'
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
    # halt the cpu- don't try to run while we change flash
    self.device.cpu.halt()
    # make sure the flash is not busy
    self.wait4complete()
    # unlock the flash
    self.unlock()
    # set the mass erase bit
    self.hw.CR.set_bit(self.CR_MER)
    # set the start bit
    self.hw.CR.set_bit(self.CR_STRT)
    # wait for completion
    error = self.wait4complete()
    # clear the mass erase bit
    self.hw.CR.clr_bit(self.CR_MER)
    # lock the flash
    self.lock()
    return (1,0)[error is None]

  def erase(self, page):
    """erase a flash page - return non-zero for an error"""
    # halt the cpu- don't try to run while we change flash
    self.device.cpu.halt()
    # make sure the flash is not busy
    self.wait4complete()
    # unlock the flash
    self.unlock()
    # set the page erase bit
    self.hw.CR.set_bit(self.CR_PER)
    # set the page address
    self.hw.AR.wr(page.adr)
    # set the start bit
    self.hw.CR.set_bit(self.CR_STRT)
    # wait for completion
    error = self.wait4complete()
    # clear the page erase bit
    self.hw.CR.clr_bit(self.CR_PER)
    # lock the flash
    self.lock()
    return (1,0)[error is None]

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.pages])

#-----------------------------------------------------------------------------

class stm32l4x2(flash):
  """flash driver for STM32L4x2 devices"""

  # FLASH.SR bits
  SR_BSY = 1 << 16      # Busy
  SR_OPTVERR = 1 << 15  # Option validity error
  SR_RDERR = 1 << 14    # PCROP read error
  SR_FASTERR = 1 << 9   # Fast programming error
  SR_MISERR = 1 << 8    # Fast programming data miss error
  SR_PGSERR = 1 << 7    # Programming sequence error
  SR_SIZERR = 1 << 6    # Size error
  SR_PGAERR = 1 << 5    # Programming alignment error
  SR_WRPERR = 1 << 4    # Write protected error
  SR_PROGERR = 1 << 3   # Programming error
  SR_OPERR = 1 << 1     # Operation error
  SR_EOP = 1 << 0       # End of operation

  SR_errors = (SR_OPTVERR|SR_RDERR|SR_FASTERR|SR_MISERR|SR_PGSERR|SR_SIZERR|SR_PGAERR|SR_WRPERR|SR_PROGERR|SR_OPERR)

  # FLASH.CR bits
  CR_LOCK = 1 << 31       # FLASH_CR Lock
  CR_OPTLOCK = 1 << 30    # Options Lock
  CR_OBL_LAUNCH = 1 << 27 # Force the option byte loading
  CR_RDERRIE = 1 << 26    # PCROP read error interrupt enable
  CR_ERRIE = 1 << 25      # Error interrupt enable
  CR_EOPIE = 1 << 24      # End of operation interrupt enable
  CR_FSTPG = 1 << 18      # Fast programming
  CR_OPTSTRT = 1 << 17    # Options modification start
  CR_START = 1 << 16      # Start
  CR_MER2 = 1 << 15       # Bank 2 Mass erase
  CR_BKER = 1 << 11       # Bank erase
  # CR_PNB [10:3] Page number
  CR_MER1 = 1 << 2        # Bank 1 Mass erase
  CR_PER = 1 << 1         # Page erase
  CR_PG = 1 << 0          # Programming

  def __init__(self, device):
    self.device = device
    self.hw = self.device.FLASH
    self.pages = mem.flash_regions(self.device, flash_map[self.device.soc_name])
    self.lib = lib.stm32l4x2_flash

  def check_errors(self, status):
    """check the error bits in the status value"""
    if status & self.SR_OPTVERR:
      return 'option validity error'
    elif status & self.SR_RDERR:
      return 'PCROP read error'
    elif status & self.SR_FASTERR:
      return 'fast programming error'
    elif status & self.SR_MISERR:
      return 'fast programming data miss error'
    elif status & self.SR_PGSERR:
      return 'programming sequence error'
    elif status & self.SR_SIZERR:
      return 'size error'
    elif status & self.SR_PGAERR:
      return 'programming alignment error'
    elif status & self.SR_WRPERR:
      return 'write protected error'
    elif status & self.SR_PROGERR:
      return 'programming error'
    elif status & self.SR_OPERR:
      return 'operation error'
    return None

  # Public API

  def sector_list(self):
    """return a list of flash pages"""
    return self.pages

  def check_region(self, x):
    """return None if region x meets the flash write requirements"""
    # Flash writing on this chip is 64-bits at a time with 64 bit alignment.
    if x.adr & 7:
      return 'memory region is not 64-bit aligned'
    if x.size & 7:
      return 'memory region is not a multiple of 64-bits'
    # check that we are within flash
    if self.device.flash_main.contains(x):
      return None
    return 'memory region is not within flash'

  def firmware_region(self):
    """return the name of the flash region used for firmware"""
    return 'flash_main'

  def erase_all(self):
    """erase all - return non-zero for an error"""
    # halt the cpu- don't try to run while we change flash
    self.device.cpu.halt()
    # make sure the flash is not busy
    self.wait4complete()
    # unlock the flash
    self.unlock()
    # set the mass erase bit
    self.hw.CR.set_bit(self.CR_MER1)
    # set the start bit
    self.hw.CR.set_bit(self.CR_START)
    # wait for completion
    error = self.wait4complete()
    # clear the mass erase bit
    self.hw.CR.clr_bit(self.CR_MER1)
    # lock the flash
    self.lock()
    return (1,0)[error is None]

  def erase(self, page):
    """erase a flash page - return non-zero for an error"""
    # halt the cpu- don't try to run while we change flash
    self.device.cpu.halt()
    # make sure the flash is not busy
    self.wait4complete()
    # unlock the flash
    self.unlock()
    # set the page number and page erase bit
    self.hw.CR.wr((page.meta.page << 3) | self.CR_PER)
    # set the start bit
    self.hw.CR.set_bit(self.CR_START)
    # wait for completion
    error = self.wait4complete()
    # clear the page erase bit
    self.hw.CR.clr_bit(self.CR_PER)
    # lock the flash
    self.lock()
    return (1,0)[error is None]

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.pages])

#-----------------------------------------------------------------------------

class sdrv(object):
  """flash driver for STM32F4xxx sector based devices"""

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
  VOLTS_18_21     = 0 << 8 # 1.8V to 2.1V, 8-bit writes
  VOLTS_21_27     = 1 << 8 # 2.1V to 2.7V, 16-bit writes
  VOLTS_27_36     = 2 << 8 # 2.7V to 3.6V, 32-bit writes
  VOLTS_27_36_VPP = 3 << 8 # 2.7V to 3.6V + Ext Vpp, 64-bit writes
  # FLASH.CR.CR_PSIZE write size
  PSIZE_BYTE        = 0 << 8 # 8 bits
  PSIZE_HALF_WORD   = 1 << 8 # 16 bits
  PSIZE_WORD        = 2 << 8 # 32 bits
  PSIZE_DOUBLE_WORD = 3 << 8 # 64 bits

  def __init__(self, device):
    self.device = device
    self.hw = self.device.FLASH
    self.sectors = mem.flash_regions(self.device, flash_map[self.device.soc_name])
    # the target voltage controls the erase/write parallelism
    v = self.device.cpu.dbgio.target_voltage()
    if v >= 2700:
      self.volts = self.VOLTS_27_36
      self.lib = lib.stm32f4_32_flash
    elif v >= 2100:
      self.volts = self.VOLTS_21_27
      self.lib = lib.stm32f4_16_flash
    else:
      self.volts = self.VOLTS_18_21
      self.lib = lib.stm32f4_8_flash

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
    elif status & self.SR_PGSERR:
      return 'program sequence error'
    elif status & self.SR_PGPERR:
      return 'program parallelism error'
    elif status & self.SR_PGAERR:
      return 'program alignment error'
    elif status & self.SR_WRPERR:
      return 'write protect error'
    elif status & self.SR_OPERR:
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
    # sector number
    n = sector.meta.sector
    # Need to add offset of 4 when sector higher than 11
    if n > 11:
      n += 4
    cr |= n << 3
    self.hw.CR.wr(cr)

  def __wr_lib(self, mr, io):
    """write using asm library code (41.20 KiB/sec)"""
    # halt the cpu and load the library
    self.device.cpu.halt()
    self.device.cpu.loadlib(self.lib)
    words_to_write = mr.size / 4
    words_per_buf = self.device.rambuf.size / 4
    src = self.device.rambuf.adr
    dst = mr.adr
    while words_to_write > 0:
      # program a full buffer, or whatever is left
      n = min(words_to_write, words_per_buf)
      # copy the io buffer to the ram buffer
      self.device.cpu.wrmem32(src, n, io)
      # setup the registers and call the library
      self.device.cpu.wrreg('r0', src)
      self.device.cpu.wrreg('r1', dst)
      self.device.cpu.wrreg('r2', n)
      status = self.device.cpu.runlib(self.lib)
      # check for errors
      if status & self.SR_RDERR:
        return 'read error'
      elif status & self.SR_PGSERR:
        return 'program sequence error'
      elif status & self.SR_PGPERR:
        return 'program parallelism error'
      elif status & self.SR_PGAERR:
        return 'program alignment error'
      elif status & self.SR_WRPERR:
        return 'write protect error'
      elif status & self.SR_OPERR:
        return 'operation error'
      # next buffer
      words_to_write -= n
      dst += 4 * n
    return None

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
    # make sure the flash is not busy
    self.__wait4complete()
    # unlock the flash
    self.__unlock()
    # setup the sector erase
    self.__sector_erase(sector)
    # set the start bit
    self.hw.CR.set_bit(self.CR_STRT)
    # wait for completion
    error = self.__wait4complete(100)
    # clear any set CR bits
    self.hw.CR.wr(0)
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
    self.__wr_lib(mr, io)
    # lock the flash
    self.__lock()

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.sectors])

#-----------------------------------------------------------------------------
