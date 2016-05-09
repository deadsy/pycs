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

soc_name = 'ATSAML21J18B'
prompt = 'saml21'

# -----------------------------------------------------------------------------

class target(object):
  """saml21 - Atmel SAM L21 Xplained Pro Evaluation Board"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    info = atsam.lookup(soc_name)
    self.jlink = jlink.JLink(usb_number, info['cpu_type'], jlink._JLINKARM_TIF_SWD)
    self.cpu = cortexm.cortexm(self, ui, self.jlink, info['cpu_type'], info['priority_bits'])
    self.soc = atsam.soc(self.cpu, info)

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
      ('soc', 'system on chip functions', self.soc.menu),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.cmd_jlink(self.ui, None)

  def set_prompt(self):
    indicator = ('*', '')[self.jlink.is_halted()]
    self.ui.cli.set_prompt('\n%s%s> ' % (prompt, indicator))

  def cmd_jlink(self, ui, args):
    """display jlink information"""
    ui.put('%s\n' % self.jlink)

  def cmd_exit(self, ui, args):
    self.jlink.jlink_close()
    ui.exit()

# -----------------------------------------------------------------------------
