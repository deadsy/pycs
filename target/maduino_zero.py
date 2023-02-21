# -----------------------------------------------------------------------------
"""

Makerfabs Maduino Zero (ATSAMD21G18A)

"""
# -----------------------------------------------------------------------------

import cli
import cortexm
import mem
import soc
import flash

import vendor.atmel.atmel as atmel
import vendor.atmel.flash as flash_driver

# -----------------------------------------------------------------------------

soc_name = 'ATSAMD21G18A'
prompt = 'maduino_zero'

# -----------------------------------------------------------------------------

# jlink device
default_itf = {
  'name': 'jlink',
  'vid': 0x1366,
  'pid': 0x0101,
  'itf': 0,
}

# -----------------------------------------------------------------------------

class target(object):
  """maduino_zero - Makerfabs Maduino Zero"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = atmel.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.flash(self.device), self.device, self.mem)

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      ('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      ('program', self.flash.cmd_program, flash.help_program),
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
    self.ui.cli.set_prompt('%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------
