# -----------------------------------------------------------------------------
"""

Memory Functions

"""
# -----------------------------------------------------------------------------

import util
import iobuf

# -----------------------------------------------------------------------------

help_memdisplay = (
    ('<adr> [len]', 'address (hex)'),
    ('', 'length (hex) - default is 0x40'),
)

help_mem2file = (
    ('<adr> <len> [file]', 'address (hex)'),
    ('', 'length (hex)'),
    ('', 'filename - default is \"mem.bin\"'),
)

help_file2mem = (
    ('<adr> [file] [len]', 'address (hex)'),
    ('', 'filename - default is \"mem.bin\"'),
    ('', 'length (hex) - default is file length'),
)

help_memrd = (
    ('<adr>', 'address (hex)'),
)

help_memwr = (
    ('<adr> <val>', 'address (hex)'),
    ('', 'value (hex)'),
)

help_regs = (
    ('<name>', 'register set name'),
)

# -----------------------------------------------------------------------------

def memory_test(ui, cpu, adr, block_size, num_blocks, iters):
  """test ram memory over a given region"""
  # test a 32 bit write at the start and end of the block
  locns = [adr + (block_size * i) for i in range(num_blocks)]
  locns.extend([adr - 4 + (block_size * (i + 1)) for i in range(num_blocks)])
  max_adr = adr + (block_size * num_blocks) - 4
  ui.put('testing %d locations %08x-%08x (32 bit write/read, %d iterations)\n' % (len(locns), adr, max_adr, iters))

  for i in range(iters):
    # writing random values
    ui.put('%d: writing...\n' % i)
    saved = []
    for adr in locns:
      val = random.getrandbits(32)
      cpu.wr(adr, val, 32)
      saved.append(val)
    # reading back values
    ui.put('%d: reading...\n' % i)
    bad = 0
    for (adr, wr_val) in zip(locns, saved):
      val = cpu.rd(adr, 32)
      if val != wr_val:
        ui.put('[%08x] = %08x : should be %08x, xor %08x\n' % (adr, val, wr_val, val ^ wr_val))
        bad += 1
    # report for this iteration
    if not bad:
      ui.put('%d: passed\n' % i)
    else:
      ui.put('%d: %d of %d locations failed\n' % (i, bad, len(locns)))

# -----------------------------------------------------------------------------

class mem(object):

  def __init__(self, cpu):
    self.cpu = cpu

    self.menu = (
      ('compare', self.cmd_compare, help_file2mem),
      ('d8', self.cmd_display8, help_memdisplay),
      ('d16', self.cmd_display16, help_memdisplay),
      ('d32', self.cmd_display32, help_memdisplay),
      ('>file', self.cmd_mem2file, help_mem2file),
      ('<file', self.cmd_file2mem, help_file2mem),
      ('rd8', self.cmd_rd8, help_memrd),
      ('rd16', self.cmd_rd16, help_memrd),
      ('rd32', self.cmd_rd32, help_memrd),
      ('wr8', self.cmd_wr8, help_memwr),
      ('wr16', self.cmd_wr16, help_memwr),
      ('wr32', self.cmd_wr32, help_memwr),
    )

  def cmd_rd(self, ui, args, n):
    """memory read command for n bits"""
    if util.wrong_argc(ui, args, (1,)):
      return
    adr = util.sex_arg(ui, args[0], self.cpu.width)
    if adr == None:
      return
    adr = util.align_adr(adr, n)
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
    adr = util.align_adr(adr, n)
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
    x = util.m2f_args(ui, 32, args)
    if x is None:
      return
    (adr, n, name) = x
    # adjust the address and length
    adr = util.align_adr(adr, 32)
    n = util.nbytes_to_nwords(n, 32)
    # read memory, write to file object
    mf = iobuf.to_file(32, ui, name, n, le = True)
    self.cpu.rd_mem(adr, n, mf)
    mf.close()

  def cmd_file2mem(self, ui, args):
    """read from file, write to memory"""
    ui.put('todo\n')

  def cmd_compare(self, ui, args):
    """compare memory with a file"""
    ui.put('todo\n')

  def cmd_display8(self, ui, args):
    """display memory 8 bits"""
    x = util.m2d_args(ui, 32, args)
    if x is None:
      return
    (adr, n) = x
    # address is on a 16 byte boundary
    # n is an integral multiple of 16 bytes
    adr &= ~15
    n = (n + 15) & ~15
    n = util.nbytes_to_nwords(n, 32)
    # read memory, dump to display
    md = iobuf.to_display(32, ui, adr, le = True)
    self.cpu.rd_mem(adr, n, md)

  def cmd_display16(self, ui, args):
    """display memory 16 bits"""
    ui.put('todo\n')

  def cmd_display32(self, ui, args):
    """display memory 32 bits"""
    ui.put('todo\n')

# -----------------------------------------------------------------------------

