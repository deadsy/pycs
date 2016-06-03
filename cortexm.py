# -----------------------------------------------------------------------------
"""

Cortex-M CPU Operations

"""
# -----------------------------------------------------------------------------

import time

import util
import iobuf
import jlink

# -----------------------------------------------------------------------------

help_disassemble = (
    ('[adr] [len]', 'address (hex) - default is current pc'),
    ('', 'length (hex) - default is 0x10'),
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

# systick is a 24-bit down counter
SysTick_MAXCOUNT = (1 << 24) - 1

# -----------------------------------------------------------------------------

class cortexm(object):

  def __init__(self, target, ui, jlink, device):
    self.target = target
    self.ui = ui
    self.jlink = jlink
    self.device = device
    self.saved_regs = []
    self.width = 32

    # setup the memory mapped registers for this cpu
    self.scb = self.device.SCB
    self.systick = self.device.SysTick
    self.nvic = self.device.NVIC

    self.menu = (
      ('cpuid', self.cmd_cpuid),
      ('rate', self.cmd_systick_rate),
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

  def NVIC_GetPriority(self, irq):
    """return the priority encoding for an exception"""
    if irq == Reset_IRQn:
      return -3
    elif irq == NMI_IRQn:
      return -2
    elif irq == HardFault_IRQn:
      return -1
    elif irq < 0:
      # system exceptions
      return self.scb.rd('SHPR', irq + NUM_SYS_EXC - 4) >> (8 - self.priority_bits)
    else:
      # interrupt handlers
      return self.nvic.rd('IPR', irq) >> (8 - self.priority_bits)

  def NVIC_GetPriorityGrouping(self):
    """return the priority grouping number"""
    scb = self.get_memio('scb')
    return (scb.rd('AIRCR') >> 8) & 7

  def NVIC_DecodePriority(self, priority, group):
    """decode a priority level"""
    group &= 7
    pre_bits = (7 - group, self.priority_bits)[(7 - group) > self.priority_bits]
    sub_bits = self.priority_bits - pre_bits
    pre = (priority >> sub_bits) & ((1 << (pre_bits)) - 1)
    sub = priority & ((1 << sub_bits) - 1)
    return (pre, sub)

  def NVIC_DecodeString(self, group):
    """return a priority decode string"""
    group &= 7
    pre_bits = (7 - group, self.priority_bits)[(7 - group) > self.priority_bits]
    sub_bits = self.priority_bits - pre_bits
    s = []
    s.append('p' * pre_bits)
    s.append('s' * sub_bits)
    s.append('.' * (8 - pre_bits - sub_bits))
    s.append(' %d bits group %d' % (self.priority_bits, group))
    return ''.join(s)

  def cmd_regs(self, ui, args):
    """display cpu registers"""
    self.halt()
    regs = [self.jlink.rdreg(n) for (name, n) in _reg_names]
    if len(self.saved_regs) == 0:
      self.saved_regs = regs
    delta = [('*', '')[x == y] for (x, y) in zip(self.saved_regs, regs)]
    self.saved_regs = regs
    for i in range(len(_reg_names)):
      ui.put('%-8s: %08x %s\n' % (_reg_names[i][0], regs[i], delta[i]))

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
    md = iobuf.arm_disassemble(ui, adr)
    self.rd_mem(adr, n, md)

  def cmd_go(self, ui, args):
    """exit debug mode, run until breakpoint"""
    self.go(msg=True)

  def cmd_halt(self, ui, args):
    """stop running, enter debug mode"""
    self.halt(msg=True)

  def cmd_step(self, ui, args):
    """single step the cpu"""
    self.step()

  def systick_rate(self, t, cpuclk):
    """return the systick count after t seconds"""
    self.halt()
    # save the current settings
    saved_ctrl = self.systick.CTRL.rd()
    saved_load = self.systick.LOAD.rd()
    saved_val = self.systick.VAL.rd()
    # setup systick
    self.systick.CTRL.wr((cpuclk << 2) | (1 << 0))
    self.systick.VAL.wr(SysTick_MAXCOUNT)
    self.systick.LOAD.wr(SysTick_MAXCOUNT)
    # run for a while
    self.go()
    t_start = time.time()
    time.sleep(t)
    t = time.time() - t_start
    self.halt()
    # read the counter
    stop = self.systick.VAL.rd()
    # restore the saved settings
    self.systick.VAL.wr(saved_val)
    self.systick.LOAD.wr(saved_load)
    self.systick.CTRL.wr(saved_ctrl)
    # return the tick count and time
    return (SysTick_MAXCOUNT - stop, t)

  def measure_systick(self, ui, msg, cpuclk):
    """measure systick rate"""
    ui.put('%s clock rate: ' % msg)
    # short trial measurement that hopefully will not underflow
    (c, t) = self.systick_rate(0.05, cpuclk)
    if c:
      # longer measurement for better accuracy
      t = 0.8 * t * float(SysTick_MAXCOUNT) / float(c)
      # clamp the time to a maximum limit
      if t > 4:
        t = 4
      (c, t) = self.systick_rate(t, cpuclk)
      mhz = c / (1000000 * t)
      ui.put('%.2f Mhz\n' % mhz)
    else:
      ui.put('fail: systick did not decrement\n')

  def cmd_systick_rate(self, ui, args):
    """measure systick counter rate"""
    self.measure_systick(ui, 'external', 0)
    self.measure_systick(ui, 'cpu', 1)

  def cmd_cpuid(self, ui, args):
    """display the cpu identifier"""
    ui.put('%s\n' % self.device.SCB.CPUID.display())

# -----------------------------------------------------------------------------
# return a string for the current state of the exceptions
# This is a generic CPU function but to do this properly we need some information
# from the SoC. So- this function is not a part of the cpu object.

system_exceptions = {
  1: 'Reset',
  2: 'NMI',
  3: 'HardFault',
  4: 'MemManage',
  5: 'BusFault',
  6: 'UsageFault',
  11: 'SVCall',
  12: 'DebugMonitor',
  14: 'PendSV',
  15: 'SysTick',
}

NUM_SYS_EXC = 16

Reset_IRQn = -15
NMI_IRQn = -14
HardFault_IRQn = -13
MemManage_IRQn = -12
BusFault_IRQn = -11
UsageFault_IRQn = -10
SVCall_IRQn = -5
DebugMonitor_IRQn = -4
PendSV_IRQn = -2
SysTick_IRQn = -1

def build_exceptions(vector_table):
  """combine the system exceptions with an SoC irq vector table"""
  d = dict(system_exceptions)
  for (k, v) in vector_table.iteritems():
    d[k + NUM_SYS_EXC] = v
  return d

def exceptions_str(cpu, soc):
  s = []
  group = cpu.NVIC_GetPriorityGrouping()
  vtable = cpu.scb.rd('VTOR')
  icsr = cpu.scb.rd('ICSR')
  shcsr = cpu.scb.rd('SHCSR')

  s.append('%-19s: %s' % ('priority grouping', cpu.NVIC_DecodeString(group)))
  s.append('%-19s: %08x' % ('vector table', vtable))
  s.append('Name                 Exc Irq EPA Prio Vector')
  for i in sorted(soc.exceptions.keys()):
    l = []
    irq = i - NUM_SYS_EXC

    # name
    l.append('%-19s: ' % soc.exceptions[i])
    # exception number
    l.append('%-3d ' % i)
    # irq number
    l.append(('-   ', '%-3d ' % irq)[irq >= 0])

    # enabled/pending/active
    enabled = pending = active = -1
    if irq >= 0:
      idx = (irq >> 5) & 7
      shift = irq & 31
      enabled = (cpu.nvic.rd('ISER0', idx) >> shift) & 1
      pending = (cpu.nvic.rd('ISPR0', idx) >> shift) & 1
      active = (cpu.nvic.rd('IABR0', idx) >> shift) & 1
    else:
      if irq == NMI_IRQn:
        enabled = 1
        pending = (icsr >> 31) & 1
      elif irq == MemManage_IRQn:
        enabled = (shcsr >> 16) & 1
        pending = (shcsr >> 13) & 1
        active = (shcsr >> 0) & 1
      elif irq == BusFault_IRQn:
        enabled = (shcsr >> 17) & 1
        pending = (shcsr >> 14) & 1
        active = (shcsr >> 1) & 1
      elif irq == UsageFault_IRQn:
        enabled = (shcsr >> 18) & 1
        pending = (shcsr >> 12) & 1
        active = (shcsr >> 3) & 1
      elif irq == SVCall_IRQn:
        pending = (shcsr >> 15) & 1
        active = (shcsr >> 7) & 1
      elif irq == DebugMonitor_IRQn:
        active = (shcsr >> 8) & 1
      elif irq == PendSV_IRQn:
        pending = (icsr >> 28) & 1
      elif irq == SysTick_IRQn:
        enabled = (cpu.systick.rd('CTRL') >> 1) & 1
        pending = (icsr >> 26) & 1
    l.append(util.format_bit(enabled, 'e'))
    l.append(util.format_bit(pending, 'p'))
    l.append(util.format_bit(active, 'a'))
    l.append(' ')

    # priority
    priority = cpu.NVIC_GetPriority(irq)
    if priority < 0:
      tmp = '%-4d' % priority
    else:
      tmp = '%d.%d' % cpu.NVIC_DecodePriority(priority, group)
    l.append('%-4s ' % tmp)

    # vector
    l.append('%08x ' % (cpu.rd(vtable + (i * 4), 32) & ~1))
    s.append(''.join(l))
  return '\n'.join(s)

# -----------------------------------------------------------------------------
