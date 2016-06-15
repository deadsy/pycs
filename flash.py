#-----------------------------------------------------------------------------
"""
Flash Commands

This code is the generic front end to flash programming operations.
The vendor specific flash drivers are within the vendor directories.
Those drivers expose a common API used by this code.
"""
#-----------------------------------------------------------------------------

import util
import mem

#-----------------------------------------------------------------------------

_help_erase = (
  ('<adr> <len>', 'address (hex) length (hex)'),
  ('<name> <len>', 'region name length (hex)'),
  ('<name>', 'region name (entire region)'),
)

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, driver, device):
    self.driver = driver
    self.device = device
    self.menu = (
      #('ep', self.cmd_ep),
      #('epv', self.cmd_epv),
      ('erase', self.cmd_erase, _help_erase),
      ('info', self.cmd_info),
      ('wr', self.cmd_wr),
      #('program', self.cmd_program),
      #('verify', self.cmd_verify),
    )

  def wrbuf(self, adr, buf):
    """write a buffer of 32 bit words to the 32 bit aligned memory adr"""
    if len(buf) == 0:
      # nothing to write
      return 'no data to write'
    # check for address alignment
    if adr & 3 != 0:
      return 'write address is not 32 bit aligned'
    # the memory we want to write must be contained by one of the device flash regions
    if not self.driver.in_flash(mem.region(None, adr, len(buf))):
      return 'write is not to flash'
    # write to flash
    self.driver.wrbuf(adr, buf)

  def cmd_erase(self, ui, args):
    """erase flash"""
    x = util.mem_region_args2(ui, args, self.device)
    if x is None:
      return
    (adr, size) = x
    r = mem.region(None, adr, size)
    # build a list of regions to be erased
    erase_list = [x for x in self.driver.sector_list() if r.overlap(x)]
    if len(erase_list) == 0:
      ui.put('nothing to erase\n')
      return
    # do the erase
    ui.put('erasing : ')
    progress = util.progress(ui, 1, len(erase_list))
    n_erased = 0
    n_errors = 0
    for x in erase_list:
      n_errors += self.driver.erase(x)
      n_erased += 1
      progress.update(n_erased)
    progress.erase()
    ui.put('done (%d errors)\n' % n_errors)

  def cmd_info(self, ui,args):
    """display flash information"""
    ui.put('%s\n' % self.driver)

  def cmd_wr(self, ui,args):
    """write to flash"""
    self.wrbuf(0, (0xcafebabe, 0xdeadbeef))

  def cmd_ep(self, ui, args):
    """erase and program flash"""
    pass

  def cmd_epv(self, ui, args):
    """erase, program and verify flash"""
    pass

  def cmd_program(self, ui, args):
    """program flash"""
    pass

  def cmd_verify(self, ui, args):
    """verify flash"""
    pass

#-----------------------------------------------------------------------------
