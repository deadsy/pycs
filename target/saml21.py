# -----------------------------------------------------------------------------
"""

Target file for Atmel SAM L21 Xplained Pro Evaluation Board

ATSAML21J18B SoC

"""
# -----------------------------------------------------------------------------

import conio
import cli
import jlink
import cortexm
import mem
import soc
import flash

import vendor.atmel.atmel as atmel
import vendor.atmel.flash as flash_driver

# -----------------------------------------------------------------------------

soc_name = 'ATSAML21J18B'
prompt = 'saml21'

# -----------------------------------------------------------------------------

class target(object):
  """saml21 - Atmel SAM L21 Xplained Pro Evaluation Board"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.device = atmel.get_device(self.ui, soc_name)
    self.jlink = jlink.JLink(usb_number, self.device.cpu_info.name, jlink._JLINKARM_TIF_SWD)
    self.cpu = cortexm.cortexm(self, ui, self.jlink, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.flash(self.device), self.device, self.mem)

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('exit', self.cmd_exit),
      ('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('jlink', self.jlink.cmd_jlink),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      ('program', self.flash.cmd_program, flash.help_program),
      ('regs', self.cmd_regs, soc.help_regs),
      ('vtable', self.cpu.cmd_vtable),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.jlink.cmd_jlink(self.ui, None)

  def cmd_regs(self, ui, args):
    """display registers"""
    if len(args) == 0:
      self.cpu.cmd_regs(ui, args)
    else:
      self.device.cmd_regs(ui, args)

  def set_prompt(self):
    indicator = ('*', '')[self.jlink.is_halted()]
    self.ui.cli.set_prompt('\n%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit the application"""
    self.jlink.jlink_close()
    ui.exit()

# -----------------------------------------------------------------------------
