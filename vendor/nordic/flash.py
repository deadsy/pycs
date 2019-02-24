#-----------------------------------------------------------------------------
"""
Flash Driver for Nordic Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

2) The SVD file has the UICR region as 4KiB in size. On the chip I've looked
at the actual flash storage is 1KiB, but we maintain the lie. It's not
harmful- just be aware that you may not be able to use the whole region for
storage.

3) The UICR region doesn't erase with a normal page erase, despite what you
might think from reading the reference manual. The "erase all" can be used
to clobber it.

4) According to the datasheet we can't write a code0 region from the SWD debug
interface. So - we don't bother with code 0 regions. I don't have one in this
chip in any case (FICR.CLENR0 = 0xffffffff). In general it looks like the code0
page is deprecated.

5) There are a couple of registers (FICR) that provide flash size and page size
information. I don't read them at startup because I don't want the program to
do any hardware access during initialisation. They should be checked for
consistency with the hard coded page size and region size values.

"""
#-----------------------------------------------------------------------------

import time

import util
import mem

#-----------------------------------------------------------------------------
# Define the pages of flash memory for various devices
# Check FICR.CODEPAGESIZE for page size
# Check FICR.CODESIZE for flash size

# nRF51822
nRF51822_flash = (
  ('flash', (1<<10,) * 256),
  ('UICR', (1<<10,) * 4),
)

# nRF52832
nRF52832_flash = (
  ('flash', (4<<10,) * 128),
  ('UICR', (4<<10,) * 1),
)

# map device.soc_name to the flash map
flash_map = {
  'nRF51822': nRF51822_flash,
  'nRF52832': nRF52832_flash,
}

#-----------------------------------------------------------------------------

# NVMC.CONFIG bits
CONFIG_REN = 0 # read enable
CONFIG_WEN = 1 # write enable
CONFIG_EEN = 2 # erase enable

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, device):
    self.device = device
    self.hw = self.device.NVMC
    self.pages = mem.flash_regions(self.device, flash_map[self.device.soc_name])

  def __wait4ready(self):
    """wait for flash operation completion"""
    for i in range(5):
      if self.hw.READY.rd() & 1:
        # operation completed
        return
      time.sleep(0.1)
    assert False, 'time out waiting for flash ready'

  def sector_list(self):
    """return a list of flash pages"""
    return self.pages

  def check_region(self, x):
    """return None if region x meets the flash write requirements"""
    if x.adr & 3:
      return 'memory region is not 32-bit aligned'
    if x.size & 3:
      return 'memory region is not a multiple of 32-bits'
    # check this region against the recognised flash memory
    if self.device.flash.contains(x):
      return None
    if self.device.UICR.contains(x):
      return None
    return 'memory region is not within flash'

  def firmware_region(self):
    """return the name of the flash region used for firmware"""
    return 'flash'

  def erase_all(self):
    """erase all (flash and uicr) - return non-zero for an error"""
    # erase enable
    self.hw.CONFIG.wr(CONFIG_EEN)
    self.__wait4ready()
    # erase all
    self.hw.ERASEALL.wr(1)
    self.__wait4ready()
    # back to read only
    self.hw.CONFIG.wr(CONFIG_REN)
    self.__wait4ready()
    return 0

  def erase(self, page):
    """erase a flash page - return non-zero for an error"""
    # erase enable
    self.hw.CONFIG.wr(CONFIG_EEN)
    self.__wait4ready()
    # erase the page
    if page.name == 'flash':
      self.hw.ERASEPAGE.wr(page.adr)
    elif page.name == 'UICR':
      self.hw.ERASEUICR.wr(page.adr)
    else:
      assert False, 'unrecognised flash page name %s' % page.name
    self.__wait4ready()
    # back to read only
    self.hw.CONFIG.wr(CONFIG_REN)
    self.__wait4ready()
    return 0

  def write(self, mr, io):
    """write memory region with data from an io buffer"""
    assert io.has_rd(32), 'bad buffer width'
    # write enable
    self.hw.CONFIG.wr(CONFIG_WEN)
    self.__wait4ready()
    # write the data
    self.device.cpu.wrmem(mr.adr, mr.size >> 2, io)
    self.__wait4ready()
    # back to read only
    self.hw.CONFIG.wr(CONFIG_REN)
    self.__wait4ready()

  def __str__(self):
    return util.display_cols([x.col_str() for x in self.pages])

#-----------------------------------------------------------------------------
