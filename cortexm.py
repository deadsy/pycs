# -----------------------------------------------------------------------------
"""

Cortex-M CPU Operations

"""
# -----------------------------------------------------------------------------

import time

import util
import iobuf
import cmregs
import soc

# -----------------------------------------------------------------------------

help_disassemble = (
    ('[adr] [len]', 'address (hex) - default is current pc'),
    ('', 'length (hex) - default is 0x10'),
)

# -----------------------------------------------------------------------------
# standard register names

regnames = (
  'r0','r1','r2','r3','r4','r5','r6','r7',
  'r8','r9','r10','r11','r12','r13','r14','r15',
  'lr','pc','psr','msp','psp','primask',
  'faultmask','basepri','control',
)

# -----------------------------------------------------------------------------
# System Exceptions

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

# name, number
_system_exceptions = (
  ('Reset', Reset_IRQn),
  ('NMI', NMI_IRQn),
  ('HardFault', HardFault_IRQn),
  ('MemManage', MemManage_IRQn),
  ('BusFault', BusFault_IRQn),
  ('UsageFault', UsageFault_IRQn),
  ('SVCall', SVCall_IRQn),
  ('DebugMonitor', DebugMonitor_IRQn),
  ('PendSV', PendSV_IRQn),
  ('SysTick', SysTick_IRQn),
)

def add_system_exceptions(device):
  """Add the system exceptions to the interrupt dictionary"""
  for (name, irq) in _system_exceptions:
    i = soc.interrupt()
    i.name = name
    i.description = None
    i.irq = irq
    # add it to the device
    i.parent = device
    device.interrupts[i.name] = i

def find_irq(i_list, irq):
  """return the index number of the interrupt list element matching irq"""
  n = 0
  for i in i_list:
    if i.irq == irq:
      return n
    n += 1
  return None

# -----------------------------------------------------------------------------

class cortexm(object):

  def __init__(self, target, ui, dbgio, device):
    self.target = target
    self.ui = ui
    self.dbgio = dbgio
    self.device = device
    self.saved_regs = []
    self.width = 32
    self.priority_bits = self.device.cpu_info.nvicPrioBits

    self.menu = (
      ('cpuid', self.cmd_cpuid),
      ('rate', self.cmd_systick_rate),
    )

  def rd(self, adr, n):
    """read from memory - n bits aligned"""
    adr = util.align(adr, n)
    if n == 32:
      return self.dbgio.rd32(adr)
    elif n == 16:
      return self.dbgio.rd16(adr)
    elif n == 8:
      return self.dbgio.rd8(adr)
    else:
      return 0

  def wr(self, adr, val, n):
    """write to memory - n bits aligned"""
    adr = util.align(adr, n)
    if n == 32:
      return self.dbgio.wr32(adr, val)
    elif n == 16:
      return self.dbgio.wr16(adr, val)
    elif n == 8:
      return self.dbgio.wr8(adr, val)
    else:
      return 0

  def rdmem32(self, adr, n, io):
    """read n 32 bit words from memory starting at adr"""
    max_words = 16
    while n > 0:
      nwords = (n, max_words)[n >= max_words]
      [io.wr32(x) for x in self.dbgio.rdmem32(adr, nwords)]
      n -= nwords
      adr += nwords * 4

  def wrmem32(self, adr, n, io):
    """write n 32 bit words to memory starting at adr"""
    self.dbgio.wrmem32(adr, [io.rd32() for i in range(n)])

  def halt(self, msg=False):
    """halt the cpu"""
    if self.dbgio.is_halted():
      if msg:
        self.ui.put('cpu is already halted\n')
      return
    self.dbgio.halt()
    self.target.set_prompt()

  def go(self, msg=False):
    """un-halt the cpu"""
    if not self.dbgio.is_halted():
      if msg:
        self.ui.put('cpu is already running\n')
      return
    self.dbgio.go()
    self.target.set_prompt()

  def reset(self):
    """reset the cpu"""
    self.dbgio.reset()

  def step(self):
    """single step the cpu"""
    self.dbgio.step()

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
      return self.device.SCB.SHPR1.rd8(irq + NUM_SYS_EXC - 4) >> (8 - self.priority_bits)
    else:
      # interrupt handlers
      return self.device.NVIC.IPR0.rd8(irq) >> (8 - self.priority_bits)

  def NVIC_GetPriorityGrouping(self):
    """return the priority grouping number"""
    return (self.device.SCB.AIRCR.rd() >> 8) & 7

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
    regs = [self.dbgio.rdreg(name) for name in regnames]
    if len(self.saved_regs) == 0:
      self.saved_regs = regs
    delta = [('*', '')[x == y] for (x, y) in zip(self.saved_regs, regs)]
    self.saved_regs = regs
    cols = []
    for i in range(len(regnames)):
      if regs[i] is None:
        # we don't know this register value
        continue
      cols.append([regnames[i], ': %08x' % regs[i], delta[i]])
    ui.put('%s\n' % util.display_cols(cols))

  def cmd_disassemble(self, ui, args):
    """disassemble memory"""
    if util.wrong_argc(ui, args, (0, 1, 2)):
      return
    n = 16
    if len(args) == 0:
      # read the pc
      self.halt()
      adr = self.dbgio.rd_pc()
    if len(args) >= 1:
      adr = util.sex_arg(ui, args[0], 32)
      if adr is None:
        return
    if len(args) == 2:
      n = util.int_arg(ui, args[1], (1, 2048), 16)
      if n is None:
        return
    # align the address to 32 bits
    adr = util.align(adr, 32)
    # disassemble
    md = iobuf.arm_disassemble(ui, adr)
    self.rdmem32(adr, n, md)

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
    systick = self.device.SysTick
    # save the current settings
    saved_ctrl = systick.CTRL.rd()
    saved_load = systick.LOAD.rd()
    saved_val = systick.VAL.rd()
    # setup systick
    systick.CTRL.wr((cpuclk << 2) | (1 << 0))
    systick.VAL.wr(cmregs.SysTick_MAXCOUNT)
    systick.LOAD.wr(cmregs.SysTick_MAXCOUNT)
    # run for a while
    self.go()
    t_start = time.time()
    time.sleep(t)
    t = time.time() - t_start
    self.halt()
    # read the counter
    stop = systick.VAL.rd()
    # restore the saved settings
    systick.VAL.wr(saved_val)
    systick.LOAD.wr(saved_load)
    systick.CTRL.wr(saved_ctrl)
    # return the tick count and time
    return (cmregs.SysTick_MAXCOUNT - stop, t)

  def measure_systick(self, ui, msg, cpuclk):
    """measure systick rate"""
    ui.put('%s clock rate: ' % msg)
    # short trial measurement that hopefully will not underflow
    (c, t) = self.systick_rate(0.05, cpuclk)
    if c:
      # longer measurement for better accuracy
      t = 0.8 * t * float(cmregs.SysTick_MAXCOUNT) / float(c)
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
    """display cpu identifier"""
    ui.put('%s\n' % self.device.SCB.display('CPUID', fields = True))

  def cmd_vtable(self, ui, args):
    """display exceptions vector table"""
    s = []
    group = self.NVIC_GetPriorityGrouping()
    vtable = self.device.SCB.VTOR.rd()
    icsr = self.device.SCB.ICSR.rd()
    shcsr = self.device.SCB.SHCSR.rd()

    s.append('priority group : %s' % self.NVIC_DecodeString(group))
    s.append('vector table   : %08x' % vtable)
    s.append('')
    ui.put('%s\n' % '\n'.join(s))

    i_list = self.device.interrupt_list()
    # stip superfluous prefix/suffix from external interrupt names
    names = [i.name for i in i_list]
    # don't include the system exceptions
    k = find_irq(i_list, 0)
    irq_names = names[k:]
    util.rm_prefix(irq_names, ('INT_',))
    util.rm_suffix(irq_names, ('_IRQ',))
    names[k:] = irq_names

    clist = []
    clist.append(['Name','  Exc','Irq','EPA','Prio','Vector', ''])

    for (name, i) in zip(names, i_list):
      irq = i.irq
      n = i.irq + NUM_SYS_EXC
      exc_n = ': %d' % n
      irq_n = ('-', '%d' % irq)[irq >= 0]
      # enabled/pending/active
      enabled = pending = active = -1
      if irq >= 0:
        idx = (irq >> 5) & 7
        shift = irq & 31
        enabled = (self.device.NVIC.ISER0.rd(idx) >> shift) & 1
        pending = (self.device.NVIC.ISPR0.rd(idx) >> shift) & 1
        active = (self.device.NVIC.IABR0.rd(idx) >> shift) & 1
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
          enabled = (self.device.SysTick.CTRL.rd() >> 1) & 1
          pending = (icsr >> 26) & 1
      l = []
      l.append(util.format_bit(enabled, 'e'))
      l.append(util.format_bit(pending, 'p'))
      l.append(util.format_bit(active, 'a'))
      epa = ''.join(l)
      # priority
      priority = self.NVIC_GetPriority(irq)
      if priority < 0:
        prio = '%d' % priority
      else:
        prio = '%d.%d' % self.NVIC_DecodePriority(priority, group)
      # vector
      vector = '%08x' % (self.rd(vtable + (n * 4), 32) & ~1)
      clist.append([name, exc_n, irq_n, epa, prio, vector, i.description])
    ui.put('%s\n' % util.display_cols(clist, [0,0,0,0,0,0,0]))

# -----------------------------------------------------------------------------
