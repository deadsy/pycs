# -----------------------------------------------------------------------------
"""

Nucleo-F091RC (STM32F091xC)

"""
# -----------------------------------------------------------------------------

import conio
import cli
import cortexm
import mem
import soc
import flash
import gpio

import vendor.st.st as vendor
import vendor.st.flash as flash_driver
import vendor.st.gpio as gpio_driver

# -----------------------------------------------------------------------------

soc_name = 'STM32F091xC'
prompt = 'nucleo-f091rc'

# -----------------------------------------------------------------------------

# built in stlinkv2
default_itf = {
  'name': 'stlink',
  'vid': 0x0483,
  'pid': 0x374B,
  'itf': 1,
}

# -----------------------------------------------------------------------------

# pin, mode, pupd, otype, ospeed, name
gpio_cfg = (
)

# -----------------------------------------------------------------------------

class target(object):
  """nucleo-f091rc Nucleo64 Board with STM32F091RC SoC"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    #self.flash = flash.flash(flash_driver.stm32l4x2(self.device), self.device, self.mem)
    #gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    #self.gpio = gpio.gpio(gpio_drv)

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      #('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      #('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      #('program', self.flash.cmd_program, flash.help_program),
      ('regs', self.cmd_regs, soc.help_regs),
      ('vtable', self.cpu.cmd_vtable),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.dbgio.cmd_info(self.ui, None)

  def cmd_regs(self, ui, args):
    """display registers"""
    if len(args) == 0:
      self.cpu.cmd_regs(ui, args)
    else:
      self.device.cmd_regs(ui, args)

  def set_prompt(self):
    indicator = ('*', '')[self.dbgio.is_halted()]
    self.ui.cli.set_prompt('\n%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------
