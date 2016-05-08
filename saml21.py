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
import atsam

# -----------------------------------------------------------------------------

class target(object):
  """saml21 - Atmel SAM L21 Xplained Pro Evaluation Board"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.jlink = jlink.JLink(usb_number, 'cortex-m0+', jlink._JLINKARM_TIF_SWD)
    self.cpu = cortexm.cortexm(self, ui, self.jlink)
    self.soc = atsam.soc(self.cpu, 'ATSAML21J18B')

    self.menu_root = (
      ('cpu', 'cpu functions', self.cpu.menu_cpu),
      ('da', 'disassemble memory', self.cpu.cmd_disassemble, cortexm._help_disassemble),
      ('exit', 'exit the application', self.cmd_exit),
      ('go', 'exit debug mode, run until breakpoint', self.cpu.cmd_go),
      ('halt', 'stop running, enter debug mode', self.cpu.cmd_halt),
      ('help', 'general help', self.ui.cmd_help),
      ('jlink', 'jlink information', self.cmd_jlink),
      ('mem', 'memory functions', self.cpu.menu_memory),
      ('regs', 'general registers', self.cpu.cmd_user_registers),
      ('soc', 'soc functions', self.soc.menu),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.cmd_jlink(self.ui, None)

  def set_prompt(self):
    self.ui.cli.set_prompt(('\nsaml21*> ', '\nsaml21> ')[self.jlink.is_halted()])

  def cmd_jlink(self, ui, args):
    """display jlink information"""
    ui.put('%s\n' % self.jlink)

  def cmd_exit(self, ui, args):
    self.jlink.jlink_close()
    ui.exit()

# -----------------------------------------------------------------------------
