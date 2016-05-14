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
import mem

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
    self.mem = mem.mem(self.cpu, self.soc)

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('exit', self.cmd_exit),
      ('go', self.cpu.cmd_go),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('jlink', self.jlink.cmd_jlink),
      ('mem', self.mem.menu, 'memory functions'),
      ('regs', self.cpu.cmd_regs),
      ('soc', self.soc.menu, 'system on chip functions'),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.jlink.cmd_jlink(self.ui, None)

  def set_prompt(self):
    indicator = ('*', '')[self.jlink.is_halted()]
    self.ui.cli.set_prompt('\n%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    self.jlink.jlink_close()
    ui.exit()

# -----------------------------------------------------------------------------
