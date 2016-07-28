# -----------------------------------------------------------------------------
"""
Memory Functions
"""
# -----------------------------------------------------------------------------

import math
import util
import iobuf
import time
import random

# -----------------------------------------------------------------------------

_help_mem_2file = (
  ('<filename> <address/name> [len]', 'read from memory, write to file'),
  ('  filename', 'name of file'),
  ('  address', 'address of memory (hex)'),
    ('  name', 'name of memory region - see "map" command'),
  ('  len', 'length of memory region (hex)'),
)

_help_mem_verify = (
  ('<filename> <address/name> [len]', 'read from file, verify against memory'),
  ('  filename', 'name of file'),
  ('  address', 'address of memory (hex)'),
  ('  name', 'name of memory region - see "map" command'),
  ('  len', 'length of memory region (hex) - defaults to filesize'),
)

_help_mem_region = (
  ('<address/name> <len>', 'memory region'),
  ('  address', 'address of memory (hex)'),
  ('  name', 'name of memory region - see "map" command'),
  ('  len', 'length of memory region (hex) - defaults to region size or 0x40'),
)

_help_mem_rd = (
  ('<adr>', 'address (hex)'),
)

_help_mem_wr = (
  ('<adr> <val>', 'address (hex)'),
  ('', 'value (hex)'),
)

# -----------------------------------------------------------------------------

class region(object):
  """class to represent a memory region"""

  # note: The meta data is used to store device specific region information
  # e.g. a flash sector/bank number used in a flash erase routine

  def __init__(self, name, adr, size, meta = None):
    self.name = name
    self.adr = adr
    self.size = size
    self.end = self.adr + self.size - 1
    self.meta = meta

  def overlap(self, x):
    """return True if this region and x overlap"""
    return max(self.adr, x.adr) <= min(self.end, x.end)

  def col_str(self):
    """return a 4 string column for this region [name, range, size, meta]"""
    meta_str = (str(self.meta), '')[self.meta is None]
    return [self.name, ': %08x %08x' % (self.adr, self.end), util.memsize(self.size), meta_str]

# -----------------------------------------------------------------------------

def flash_regions(device, region_map):
  """divide the named memory into sized memory regions"""
  regions = []
  for x in region_map:
    if len(x) == 2:
      # no meta information: set it all to None
      (name, region_sizes) = x
      meta = (None,) * len(region_sizes)
    elif len(x) == 3:
      # provided meta information - make sure it's per region
      (name, region_sizes, meta) = x
      assert len(region_sizes) == len(meta), 'need meta information for each flash region'
    else:
      assert False, 'bad flash region specification'
    # the regions are based on the peripheral memory space
    base_adr = device.peripherals[name].address
    total_size = device.peripherals[name].size
    adr = base_adr
    for (s, m) in zip(region_sizes, meta):
      regions.append(region(name, adr, s, m))
      adr += s
    # make sure the regions cover the entire memory space of the peripheral
    assert base_adr + total_size == adr, "regions don't encompass all memory"
  return regions

# -----------------------------------------------------------------------------

class mem(object):

  def __init__(self, cpu):
    self.cpu = cpu

    self.menu = (
      ('d8', self.cmd_display8, _help_mem_region),
      ('d16', self.cmd_display16, _help_mem_region),
      ('d32', self.cmd_display32, _help_mem_region),
      ('>file', self.cmd_mem2file, _help_mem_2file),
      ('md5', self.cmd_md5, _help_mem_region),
      ('pic', self.cmd_pic, _help_mem_region),
      ('rd8', self.cmd_rd8, _help_mem_rd),
      ('rd16', self.cmd_rd16, _help_mem_rd),
      ('rd32', self.cmd_rd32, _help_mem_rd),
      ('t8', self.cmd_test8, _help_mem_region),
      ('t16', self.cmd_test16, _help_mem_region),
      ('t32', self.cmd_test32, _help_mem_region),
      ('verify', self.cmd_verify, _help_mem_verify),
      ('wr8', self.cmd_wr8, _help_mem_wr),
      ('wr16', self.cmd_wr16, _help_mem_wr),
      ('wr32', self.cmd_wr32, _help_mem_wr),
    )

  def cmd_rd(self, ui, args, n):
    """memory read command for n bits"""
    if util.wrong_argc(ui, args, (1,)):
      return
    adr = util.sex_arg(ui, args[0], self.cpu.width)
    if adr == None:
      return
    adr = util.align(adr, n)
    ui.put('[0x%08x] = ' % adr)
    ui.put('0x%%0%dx\n' % (n/4) % self.cpu.rd(adr, n))

  def cmd_rd8(self, ui, args):
    """read 8 bits"""
    self.cmd_rd(ui, args, 8)

  def cmd_rd16(self, ui, args):
    """read 16 bits"""
    self.cmd_rd(ui, args, 16)

  def cmd_rd32(self, ui, args):
    """read 32 bits"""
    self.cmd_rd(ui, args, 32)

  def cmd_wr(self, ui, args, n):
    """memory write command for n bits"""
    if util.wrong_argc(ui, args, (1,2)):
      return
    adr = util.sex_arg(ui, args[0], self.cpu.width)
    if adr == None:
      return
    adr = util.align(adr, n)
    val = 0
    if len(args) == 2:
      val = util.int_arg(ui, args[1], util.limit_32, 16)
      if val == None:
        return
    val = util.mask_val(val, n)
    self.cpu.wr(adr, val, n)
    ui.put('[0x%08x] = ' % adr)
    ui.put('0x%%0%dx\n' % (n/4) % val)

  def cmd_wr8(self, ui, args):
    """write 8 bits"""
    self.cmd_wr(ui, args, 8)

  def cmd_wr16(self, ui, args):
    """write 16 bits"""
    self.cmd_wr(ui, args, 16)

  def cmd_wr32(self, ui, args):
    """write 32 bits"""
    self.cmd_wr(ui, args, 32)

  def cmd_mem2file(self, ui, args):
    """read from memory, write to file"""
    x = util.file_mem_args(ui, args, self.cpu.device)
    if x is None:
      return
    (name, adr, size) = x
    if size is None:
      ui.put('invalid length')
      return
    # adjust the address and length
    adr = util.align(adr, 32)
    n = util.nbytes_to_nwords(size, 32)
    # read memory, write to file object
    mf = iobuf.write_file(ui, 'writing to %s' % name, name, n * 4)
    self.cpu.rdmem32(adr, n, mf)
    mf.close()

  def cmd_verify(self, ui, args):
    """verify memory against file"""
    x = util.file_mem_args(ui, args, self.cpu.device)
    if x is None:
      return
    (name, adr, size) = x
    # check the file
    filesize = util.file_arg(ui, name)
    if filesize is None:
      return
    # round up the filesize - the io object will return 0xff for any bytes beyond EOF
    filesize = util.roundup(filesize, 32)
    if size is None:
      # no length on the command line - verify the filesize
      size = filesize
    if size > filesize:
      # region is larger than file - just verify the filesize
      size = filesize
    # adjust the address and length
    adr = util.align(adr, 32)
    n = util.nbytes_to_nwords(size, 32)
    # read memory, verify against file object
    mf = iobuf.verify_file(ui, 'verify %s (%d bytes):' % (name, n * 4), name, n * 4)
    self.cpu.rdmem32(adr, n, mf)
    mf.close()

  def __display(self, ui, args, width):
    """display memory: as width bits"""
    x = util.mem_args(ui, args, self.cpu.device)
    if x is None:
      return
    (adr, n) = x
    if n == 0:
      return
    if n is None:
      n = 0x40
     # round down address to 16 byte boundary
    adr &= ~15
    # round up n to an integral multiple of 16 bytes
    n = (n + 15) & ~15
    # print the header
    if width == 8:
      ui.put('address   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F\n')
    elif width == 16:
      ui.put('address   0    2    4    6    8    A    C    E\n')
    elif width == 32:
      ui.put('address   0        4        8        C\n')
    else:
      assert False, 'bad width'
    # read and print the data
    for i in xrange(n/16):
      # read 4, 32-bit words (16 bytes per line)
      io = iobuf.data_buffer(32)
      self.cpu.rdmem(adr, 4, io)
      # work out the data string
      io.convert(width, 'le')
      data_str = str(io)
      # work out the ascii string
      io.convert(8, 'le')
      ascii_str = io.ascii_str()
      ui.put('%08x: %s  %s\n' % (adr, data_str, ascii_str))
      adr += 16

  def cmd_display8(self, ui, args):
    """display memory 8 bits"""
    self.__display(ui, args, 8)

  def cmd_display16(self, ui, args):
    """display memory 16 bits"""
    self.__display(ui, args, 16)

  def cmd_display32(self, ui, args):
    """display memory 32 bits"""
    self.__display(ui, args, 32)

  def __analyze(self, buf, ofs, n):
    """return a character to respresent the buffer"""
    b0 = buf[ofs]
    if b0 is None:
      c = ' '
    elif b0 == 0:
      c = '-'
    elif b0 == 0xff:
      c = '.'
    else:
      c = '$'
    for i in range(1, n):
      k = buf[ofs + i]
      if k is not None and k != b0:
        return '$'
    return c

  def cmd_pic(self, ui, args):
    """display a pictorial summary of memory"""
    x = util.mem_args(ui, args, self.cpu.device)
    if x is None:
      return
    (adr, n) = x
    if n == 0:
      return
    if n is None:
      n = 0x40
    # round down address to 32-bit byte boundary
    adr &= ~3
    # round up n to an integral multiple of 4 bytes
    n = (n + 3) & ~3
    # work out how many rows, columns and bytes per symbol we should display
    cols_max = 70
    cols = cols_max + 1
    bps = 1
    # we try to display a matrix that is roughly square
    while cols > cols_max:
      bps *= 2
      cols = int(math.sqrt(float(n)/float(bps)))
    rows = int(math.ceil(n / (float(cols) * float(bps))))
    # bytes per row
    bpr = cols * bps
    # work out the none padding
    nwords = n / 4
    nwords_displayed = (((cols * rows * bps) + 3) & ~3) / 4
    none_pad = [None,] * ((nwords_displayed - nwords) * 4)
    # read the memory
    if n > (16 << 10):
      ui.put('reading memory ...\n')
    data = iobuf.data_buffer(32)
    self.cpu.rdmem32(adr, nwords, data)
    data.convert8(mode = 'le')
    # add the none padding
    data.buf.extend(none_pad)
    # display the summary
    ui.put("'.' all ones, '-' all zeroes, '$' various\n")
    ui.put('%d (0x%x) bytes per symbol\n' % (bps, bps))
    ui.put('%d (0x%x) bytes per row\n' % (bpr, bpr))
    ui.put('%d cols x %d rows\n' % (cols, rows))
    # display the matrix
    ofs = 0
    for y in range(rows):
      s = []
      adr_str = '0x%08x: ' % (adr + ofs)
      for x in range(cols):
        s.append(self.__analyze(data.buf, ofs, bps))
        ofs += bps
      ui.put('%s%s\n' % (adr_str, ''.join(s)))

  def cmd_md5(self, ui, args):
    """calculate an md5 hash of memory"""
    x = util.mem_args(ui, args, self.cpu.device)
    if x is None:
      return
    (adr, n) = x
    if n == 0:
      return
    if n is None:
      n = 0x40
    # round down address to 32-bit byte boundary
    adr &= ~3
    # round up n to an integral multiple of 4 bytes
    n = (n + 3) & ~3
    # read the memory
    if n > (16 << 10):
      ui.put('reading memory ...\n')
    data = iobuf.data_buffer(32)
    t_start = time.time()
    self.cpu.rdmem(adr, n/4, data)
    t_end = time.time()
    ui.put('%s\n' % data.md5('le'))
    ui.put('%.2f KiB/sec\n' % (float(n)/((t_end - t_start) * 1024.0)))

  def cmd_test(self, width, ui, args):
    """test memory with a write and readback"""
    x = util.mem_args(ui, args, self.cpu.device)
    if x is None:
      return
    (adr, n) = x
    if n == 0:
      return
    if n is None:
      n = 0x40
    # round down address to 32-bit byte boundary
    adr &= ~3
    # round up n to an integral multiple of 4 bytes
    n = (n + 3) & ~3
    # convert to n 32/16/8-bit units
    nx = n / (width / 8)
    maxval = (1 << width) - 1
    # we will typically be testing ram, so halt the cpu.
    self.cpu.halt()
    # build a random write buffer
    wrbuf = iobuf.data_buffer(width)
    [wrbuf.write(random.randint(0, maxval)) for i in xrange(nx)]
    # write it to memory
    t_start = time.time()
    self.cpu.wrmem(adr, nx, wrbuf)
    t_end = time.time()
    ui.put('write %.2f KiB/sec\n' % (float(n)/((t_end - t_start) * 1024.0)))
    # read it from memory
    rdbuf = iobuf.data_buffer(width)
    t_start = time.time()
    self.cpu.rdmem(adr, nx, rdbuf)
    t_end = time.time()
    ui.put('read %.2f KiB/sec\n' % (float(n)/((t_end - t_start) * 1024.0)))
    ui.put('read %s write\n' % ('!=', '==')[wrbuf.compare(rdbuf)])

  def cmd_test8(self, ui, args):
    """test memory with 8-bit write and readback"""
    self.cmd_test(8, ui, args)

  def cmd_test16(self, ui, args):
    """test memory with 16-bit write and readback"""
    self.cmd_test(16, ui, args)

  def cmd_test32(self, ui, args):
    """test memory with 32-bit write and readback"""
    self.cmd_test(32, ui, args)

# -----------------------------------------------------------------------------
