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
import iobuf

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

help_program = (
  ('<filename>', 'write a firmware file to flash'),
    ('  filename', 'name of file'),
)

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, driver, device, mem):
    self.driver = driver
    self.device = device
    self.mem = mem
    self.menu = (
      ('erase', self.cmd_erase, _help_erase),
      ('info', self.cmd_info),
      ('write', self.cmd_write, _help_write),
    )

  def cmd_erase(self, ui, args):
    """erase flash"""
    # check for erase all
    if len(args) == 1 and args[0] == '*':
      ui.put('erase all: ')
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
      return
    # round up the filesize - the io object will return 0xff for any bytes beyond EOF
    filesize = util.roundup(filesize, 32)
    if n is None:
      # no length on the command line - program the filesize
      n = filesize
    if n >= filesize:
      # region is bigger than the file - program the filesize
      n = filesize
    else:
      # region is smaller than the file - truncate the file
      ui.put('%s is larger than target memory: %d > %d bytes (truncating)\n' % (name, filesize, n))
    # make sure the target region in flash is suitable
    mr = mem.region(None, adr, n)
    msg = self.driver.check_region(mr)
    if msg is not None:
      ui.put('%s\n' % msg)
      return
    # read from file, write to memory
    mf = iobuf.read_file(ui, 'writing %s (%d bytes):' % (name, n), name, n)
    self.driver.write(mr, mf)
    mf.close(rate = True)

  def cmd_info(self, ui,args):
    """display flash information"""
    ui.put('%s\n' % self.driver)

  def cmd_program(self, ui, args):
    """program firmware file to flash"""
    if util.wrong_argc(ui, args, (1,)):
      return None
    x = util.file_arg(ui, args[0])
    if x is None:
      return
    # erase all
    self.cmd_erase(ui, ('*',))
    # write to flash
    region_name = self.driver.firmware_region()
    self.cmd_write(ui, (args[0], region_name))
    # verify against the file
    self.mem.cmd_verify(ui, (args[0], region_name))

#-----------------------------------------------------------------------------
