# -----------------------------------------------------------------------------
"""

Memory Functions

"""
# -----------------------------------------------------------------------------

import util
import io
import regs

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

  def __init__(self, cpu, soc):
    self.soc = soc
    self.cpu = cpu
    self.memmap = self.build_memmap()
    self.memio = self.build_memio()

    self.menu = (
      ('compare', self.cmd_compare, help_file2mem),
      ('d8', self.cmd_display8, help_memdisplay),
      ('d16', self.cmd_display16, help_memdisplay),
      ('d32', self.cmd_display32, help_memdisplay),
      ('>file', self.cmd_mem2file, help_mem2file),
      ('<file', self.cmd_file2mem, help_file2mem),
      ('map', self.cmd_map),
      ('regs', self.cmd_regs, help_regs),
      ('rd8', self.cmd_rd8, help_memrd),
      ('rd16', self.cmd_rd16, help_memrd),
      ('rd32', self.cmd_rd32, help_memrd),
      ('wr8', self.cmd_wr8, help_memwr),
      ('wr16', self.cmd_wr16, help_memwr),
      ('wr32', self.cmd_wr32, help_memwr),
    )

  def build_memmap(self):
    """build the combined soc/cpu memory map"""
    mm = {}
    mm.update(self.cpu.memmap)
    mm.update(self.soc.memmap)
    return mm

  def build_memio(self):
    """build memory accessors for each decodable memory region"""
    d = {}
    for (name, info) in self.memmap.items():
      (base, size, r) = info
      if isinstance(r, regs.regset):
        d[name] = regs.memio(self.cpu, base, r)
    return d

  def cmd_map(self, ui, args):
    """display memory map"""
    mm = self.memmap.items()
    # sort by address
    mm.sort(key = lambda x: x[1][0])
    next_start = None
    for (name, info) in mm:
      start = info[0]
      size = info[1]
      common_name = info[2]
      if not type(info[2]) is str:
        common_name = info[2].name
      # print a marker for gaps in the map
      if (not next_start is None) and (start != next_start):
        # reserved gap or overlap
        ui.put('%s\n' % ('...', '!!!')[start < next_start])
      # display the info for this regiion
      if size is None:
        next_start = None
        ui.put('%-16s: %08x%17s%s\n' % (name, start, '', common_name))
      else:
        next_start = start + size
        ui.put('%-16s: %08x %08x %-6s %s\n' % (name, start, next_start - 1, util.memsize(size), common_name))

  def cmd_regs(self, ui, args):
    """display memory mapped registers"""
    if len(args) == 0:
      ui.put('specify a memory region name:\n')
      ui.put('%s\n' % ' '.join(sorted(self.memio.keys())))
      return
    if util.wrong_argc(ui, args, (1,)):
      return
    # check for a valid name
    if not args[0] in self.memmap.keys():
      ui.put('no memory region with this name\n')
      return
    # check for a decodable name
    if not args[0] in self.memio.keys():
      ui.put('no decode for this memory region\n')
      return
    # display the registers
    ui.put('%s\n' % self.memio[args[0]].emit())

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
    mf = io.to_file(32, ui, name, n, le = True)
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
    md = io.to_display(32, ui, adr, le = True)
    self.cpu.rd_mem(adr, n, md)

  def cmd_display16(self, ui, args):
    """display memory 16 bits"""
    ui.put('todo\n')

  def cmd_display32(self, ui, args):
    """display memory 32 bits"""
    ui.put('todo\n')

# -----------------------------------------------------------------------------

