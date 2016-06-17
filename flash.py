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
  ('*', 'erase all'),
  ('<address/name> [len]', 'erase memory region'),
  ('  address', 'address of memory (hex)'),
  ('  name', 'name of memory region - see "map" command'),
  ('  len', 'length of memory region (hex) - defaults to region size'),
)

_help_write = (
  ('<filename> <address/name> [len]', 'write a file to flash'),
  ('  filename', 'name of file'),
  ('  address', 'address of memory (hex)'),
  ('  name', 'name of memory region - see "map" command'),
  ('  len', 'length of memory region (hex) - defaults to file size'),
)

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, driver, device):
    self.driver = driver
    self.device = device
    self.menu = (
      ('erase', self.cmd_erase, _help_erase),
      ('info', self.cmd_info),
      ('write', self.cmd_write, _help_write),
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
    # check for erase all
    if len(args) == 1 and args[0] == '*':
      ui.put('erase all : ')
      n_errors = self.driver.erase_all()
      ui.put('done (%d errors)\n' % n_errors)
      return
    # memory region erase
    x = util.mem_args(ui, args, self.device)
    if x is None:
      return
    (adr, n) = x
    if n is None:
      ui.put('bad erase length\n')
      return
    r = mem.region(None, adr, n)
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

  def cmd_write(self, ui,args):
    """write to flash"""
    x = util.file_mem_args(ui, args, self.device)
    if x is None:
      return
    (name, adr, n) = x
    # check the file
    filesize = util.file_arg(ui, name)
    if filesize is None:
      # file does not exist
      return
    if filesize == 0:
      ui.put('%s has zero size\n' % name)
      return
    if n is None:
      n = filesize
    # make sure the user has pointed to flash
    r = mem.region(None, adr, n)
    if not self.driver.in_flash(r):
      ui.put('memory region is not within flash\n')
      return
    if n >= filesize:
      # program the filesize
      n = filesize
    else:
      ui.put('%s larger than target memory (%d > %d bytes) - truncating\n' % (name, filesize, n))

    ui.put('%s 0x%x %d\n' % (name, adr, n))
    self.driver.write(None, None)


  def cmd_info(self, ui,args):
    """display flash information"""
    ui.put('%s\n' % self.driver)

#-----------------------------------------------------------------------------
