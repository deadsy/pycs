# -----------------------------------------------------------------------------
"""

Cortex-M CPU Operations

"""
# -----------------------------------------------------------------------------

import random
import time

import util
import io
import jlink
from util import reg, reg_set, fld, fld_set

# -----------------------------------------------------------------------------

_help_memdisplay = (
    ('<adr> [len]', 'address (hex)'),
    ('', 'length (hex) - default is 0x40'),
)

_help_mem2file = (
    ('<adr> <len> [file]', 'address (hex)'),
    ('', 'length (hex)'),
    ('', 'filename - default is \"mem.bin\"'),
)

_help_file2mem = (
    ('<adr> [file] [len]', 'address (hex)'),
    ('', 'filename - default is \"mem.bin\"'),
    ('', 'length (hex) - default is file length'),
)

_help_memrd = (
    ('<adr>', 'address (hex)'),
)

_help_memwr = (
    ('<adr> <val>', 'address (hex)'),
    ('', 'value (hex)'),
)

_help_disassemble = (
    ('[adr] [len]', 'address (hex) - default is current pc'),
    ('', 'length (hex) - default is 0x10'),
)

_help_enable_disable = (
    ('<cr>', 'show current state'),
    ('[0/1]', 'disable or enable'),
)

# -----------------------------------------------------------------------------

_reg_names = (
  ('r0', jlink.REG_R0),
  ('r1', jlink.REG_R1),
  ('r2', jlink.REG_R2),
  ('r3', jlink.REG_R3),
  ('r4', jlink.REG_R4),
  ('r5', jlink.REG_R5),
  ('r6', jlink.REG_R6),
  ('r7', jlink.REG_R7),
  ('r8', jlink.REG_R8_USR),
  ('r9', jlink.REG_R9_USR),
  ('r10', jlink.REG_R10_USR),
  ('r11', jlink.REG_R11_USR),
  ('r12', jlink.REG_R12_USR),
  ('sp(r13)', jlink.REG_R13_USR),
  ('lr(r14)', jlink.REG_R14_USR),
  ('pc(r15)', jlink.REG_R15_PC),
  ('cpsr', jlink.REG_CPSR),
)

# -----------------------------------------------------------------------------
# Memory mapping of Cortex-M4 Hardware

SCS_BASE        = 0xE000E000 # System Control Space Base Address
ITM_BASE        = 0xE0000000 # ITM Base Address
DWT_BASE        = 0xE0001000 # DWT Base Address
TPI_BASE        = 0xE0040000 # TPI Base Address
CoreDebug_BASE  = 0xE000EDF0 # Core Debug Base Address
SysTick_BASE    = (SCS_BASE + 0x0010) # SysTick Base Address
NVIC_BASE       = (SCS_BASE + 0x0100) # NVIC Base Address
SCB_BASE        = (SCS_BASE + 0x0D00) # System Control Block Base Address

# -----------------------------------------------------------------------------
# SysTick

r = []
r.append(reg('CTRL', 0x00, '(R/W) SysTick Control and Status Register', None))
r.append(reg('LOAD', 0x04, '(R/W) SysTick Reload Value Register', None))
r.append(reg('VAL', 0x08, '(R/W) SysTick Current Value Register', None))
r.append(reg('CALIB', 0x0c, '(R/ ) SysTick Calibration Register', None))
systick_regs = reg_set('SysTick', r)

SysTick_LOAD = (SysTick_BASE + 0x04)
SysTick_VAL = (SysTick_BASE + 0x08)

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

class cortex_m(object):

  def __init__(self, target, ui, jlink):
    self.target = target
    self.ui = ui
    self.jlink = jlink
    self.saved_regs = []
    self.width = 32

    self.menu_memory = (
      ('display', 'dump memory to display', self.cmd_mem2display, _help_memdisplay),
      ('>file', 'read from memory, write to file', self.cmd_mem2file, _help_mem2file),
      #('<file', 'read from file, write to memory', self.cmd_file2mem, _help_file2mem),
      ('rd8', 'read 8 bits', self.cmd_rd8, _help_memrd),
      ('rd16', 'read 16 bits', self.cmd_rd16, _help_memrd),
      ('rd32', 'read 32 bits', self.cmd_rd32, _help_memrd),
      ('test', 'read/write test of memory', self.cmd_memtest),
      #('verify', 'verify memory against a file', self.cmd_verify, _help_file2mem),
      ('wr8', 'write 8 bits', self.cmd_wr8, _help_memwr),
      ('wr16', 'write 16 bits', self.cmd_wr16, _help_memwr),
      ('wr32', 'write 32 bits', self.cmd_wr32, _help_memwr),
    )
    self.menu_cpu = (
      ('systick', 'systick registers', self.cmd_systick),
      ('rate', 'measure systick counter rate', self.cmd_systick_rate),
    )

  def rd(self, adr, n):
    """read from memory - n bits aligned"""
    adr = util.align_adr(adr, n)
    if n == 32:
      return self.jlink.rd32(adr)
    elif n == 16:
      return self.jlink.rd16(adr)
    elif n == 8:
      return self.jlink.rd8(adr)
    else:
      return 0

  def wr(self, adr, val, n):
    """write to memory - n bits aligned"""
    adr = util.align_adr(adr, n)
    if n == 32:
      return self.jlink.wr32(adr, val)
    elif n == 16:
      return self.jlink.wr16(adr, val)
    elif n == 8:
      return self.jlink.wr8(adr, val)
    else:
      return 0

  def rd_mem(self, adr, n, io):
    """read n 32 bit words from memory starting at adr"""
    max_words = 16
    while n > 0:
      nwords = (n, max_words)[n >= max_words]
      [io.write(x) for x in self.jlink.rdmem32(adr, nwords)]
      n -= nwords
      adr += nwords * 4

  def wr_mem(self, adr, n, io):
    """write n 32 bit words to memory starting at adr"""
    self.jlink.wrmem32(adr, [io.read() for i in range(n)])

  def halt(self, msg=False):
    """halt the cpu"""
    if self.jlink.is_halted():
      if msg:
        self.ui.put('cpu is already halted\n')
      return
    self.jlink.halt()
    self.target.set_prompt()

  def go(self, msg=False):
    """un-halt the cpu"""
    if not self.jlink.is_halted():
      if msg:
        self.ui.put('cpu is already running\n')
      return
    self.jlink.go()
    self.target.set_prompt()

  def reset(self):
    """reset the cpu"""
    self.jlink.reset()

  def step(self):
    """single step the cpu"""
    self.jlink.step()

  def cmd_rd(self, ui, args, n):
    """memory read command for n bits"""
    if util.wrong_argc(ui, args, (1,)):
      return
    adr = util.sex_arg(ui, args[0], self.width)
    if adr == None:
      return
    adr = util.align_adr(adr, n)
    ui.put('[0x%08x] = ' % adr)
    ui.put('0x%%0%dx\n' % (n/4) % self.rd(adr, n))

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
    adr = util.sex_arg(ui, args[0], self.width)
    if adr == None:
      return
    adr = util.align_adr(adr, n)
    val = 0
    if len(args) == 2:
      val = util.int_arg(ui, args[1], util.limit_32, 16)
      if val == None:
        return
    val = util.mask_val(val, n)
    self.wr(adr, val, n)
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
    """dump memory contents to a file"""
    x = util.m2f_args(ui, 32, args)
    if x is None:
      return
    (adr, n, name) = x
    # adjust the address and length
    adr = util.align_adr(adr, 32)
    n = util.nbytes_to_nwords(n, 32)
    # read memory, write to file object
    mf = io.to_file(32, ui, name, n, le=True)
    self.rd_mem(adr, n, mf)
    mf.close()

  def cmd_user_registers(self, ui, args):
    """display the arm user registers"""
    self.halt()
    regs = [self.jlink.rdreg(n) for (name, n) in _reg_names]
    if len(self.saved_regs) == 0:
      self.saved_regs = regs
    delta = [('*', '')[x == y] for (x, y) in zip(self.saved_regs, regs)]
    self.saved_regs = regs
    for i in range(len(_reg_names)):
      ui.put('%-8s: %08x %s\n' % (_reg_names[i][0], regs[i], delta[i]))

  def cmd_mem2display(self, ui, args):
    """display memory"""
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
    md = io.to_display(32, ui, adr, le=True)
    self.rd_mem(adr, n, md)

  def cmd_memtest(self, ui, args):
    """test memory"""
    block_size = util.MiB / 4
    memory_test(ui, self, self.target.ram_start, block_size, self.target.ram_size / block_size, 8)

  def cmd_disassemble(self, ui, args):
    """disassemble memory"""
    if util.wrong_argc(ui, args, (0, 1, 2)):
      return
    n = 16
    if len(args) == 0:
      # read the pc
      self.halt()
      adr = self.jlink.rd_pc()
    if len(args) >= 1:
      adr = util.sex_arg(ui, args[0], 32)
      if adr is None:
        return
    if len(args) == 2:
      n = util.int_arg(ui, args[1], (1, 2048), 16)
      if n is None:
        return
    # align the address to 32 bits
    adr = util.align_adr(adr, 32)
    # disassemble
    md = io.arm_disassemble(ui, adr)
    self.rd_mem(adr, n, md)

  def cmd_go(self, ui, args):
    self.go(msg=True)

  def cmd_halt(self, ui, args):
    self.halt(msg=True)

  def cmd_step(self, ui, args):
    self.step()

  def cmd_systick(self, ui, args):
    """display systick registers"""
    ui.put('%s\n' % systick_regs.emit(self, SysTick_BASE))

  def cmd_systick_rate(self, ui, args):
    """measure systick rate"""
    # We compare the host time against the systick counter to work
    # out the update frequency. The start/stop times are a bit loose
    # with the result that the determined frequency will be a slight
    # over-estimate.
    ui.put('measuring systick rate ...\n')
    # zero the counter
    self.halt()
    saved_load = self.rd(SysTick_LOAD, 32)
    start = (1 << 24) - 1
    self.wr(SysTick_LOAD, start, 32)
    self.wr(SysTick_VAL, 0, 32)
    # run for a while
    self.go()
    t_start = time.time()
    time.sleep(2.0)
    t = time.time() - t_start
    self.halt()
    # read the counter
    stop = self.rd(SysTick_VAL, 32)
    self.wr(SysTick_LOAD, saved_load, 32)
    c = start - stop
    ui.put('%d counts in %f secs\n' % (c, t))
    mhz = c / (1000000 * t)
    ui.put('%.2f Mhz\n' % mhz)

# -----------------------------------------------------------------------------
