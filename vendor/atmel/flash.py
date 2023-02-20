#-----------------------------------------------------------------------------
"""
Flash Driver for Atmel Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

2) The erase unit is a row. The write unit is a page. There are 4 pages per row.
Each page is 64 bytes.

"""
#-----------------------------------------------------------------------------

import time

import util
import mem

#-----------------------------------------------------------------------------
# Define the rows of flash memory for various devices

ATSAML21J18B_flash = (
  ('flash', (256,) * 1024),
)

ATSAMD21G18A_flash = (
  ('flash', (64,) * 4096),
)

# map device.soc_name to the flash map
flash_map = {
  'ATSAML21J18B': ATSAML21J18B_flash,
  'ATSAMD21G18A': ATSAMD21G18A_flash,
}

#-----------------------------------------------------------------------------

POLL_MAX = 5
POLL_TIME = 0.1

#-----------------------------------------------------------------------------

class flash(object):

  # NVMCTRL.INTFLAG bits
  INTFLAG_ERROR = 1 << 1 # Error
  INTFLAG_READY = 1 << 0 # NVM Ready

  # NVMCTRL.STATUS bits
  STATUS_SB = 1 << 8     # Security Bit Status
  STATUS_NVME = 1 << 4   # NVM Error
  STATUS_LOCKE = 1 << 3  # Lock Error Status
  STATUS_PROGE = 1 << 2  # Programming Error Status
  STATUS_LOAD = 1 << 1   # NVM Page Buffer Active Loading
  STATUS_PRM = 1 << 0    # Power Reduction Mode
  STATUS_ERRORS = (STATUS_NVME | STATUS_LOCKE | STATUS_PROGE)

  # NVMCTRL.CTRLA bits
  CMDEX_KEY = 0xa5 << 8 # command execution key
  CMD_ER = 0x02         # erase row
  CMD_WP = 0x04         # write page
  CMD_EAR = 0x05        # erase auxiliary row

  def __init__(self, device):
    self.device = device
    self.hw = self.device.NVMCTRL
    self.rows = mem.flash_regions(self.device, flash_map[self.device.soc_name])

  def __wait4complete(self, timeout = POLL_MAX):
    """wait for flash operation completion"""
    n = 0
    while n < POLL_MAX:
      intflag = self.hw.INTFLAG.rd()
      if intflag & self.INTFLAG_READY == 1:
        break
      time.sleep(POLL_TIME)
      n += 1
    # clear INTFLAG bits
    if intflag & self.INTFLAG_ERROR:
      self.hw.INTFLAG.wr(self.INTFLAG_ERROR)
    # read status
    status = self.hw.STATUS.rd()
    if status & self.STATUS_ERRORS:
      self.hw.STATUS.wr(self.STATUS_ERRORS)
    # check for errors
    if n >= POLL_MAX:
      return 'timeout'
    if status & self.STATUS_LOCKE:
      return 'lock error'
    if status & self.STATUS_NVME:
      return 'nvm error'
    if status & self.STATUS_PROGE:
      return 'program error'
    # done
    return None

  def sector_list(self):
    """return a list of flash rows"""
    return self.rows

  def check_region(self, x):
    """return None if region x meets the flash write requirements"""
    return None

  def firmware_region(self):
    """return the name of the flash region used for firmware"""
    return 'flash'

  def erase_all(self):
    """erase all - return the number of errors"""
    n_errors = 0
    for r in self.rows:
      n_errors += self.erase(r)
    return n_errors

  def erase(self, row):
    """erase a flash row - return non-zero for an error"""
    # make sure the flash is not busy
    self.__wait4complete()
    # set the row address
    self.hw.ADDR.wr(row.adr)
    # issue the row erase command
    self.hw.CTRLA.wr(self.CMDEX_KEY | self.CMD_ER)
    # wait for completion
    error = self.__wait4complete()
    return (1,0)[error is None]

  def write(self, mr, io):
    """write memory region with data from an io buffer"""
    pass

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.rows])

#-----------------------------------------------------------------------------
