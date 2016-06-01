# -----------------------------------------------------------------------------
"""

Target file for mb997c

STM32F4 Discovery Board with STM32F407xx SoC

"""
# -----------------------------------------------------------------------------

import conio
import cli
import jlink
import cortexm
import mem
import vendor.st.st as soc

# -----------------------------------------------------------------------------

soc_name = 'STM32F407xx'
prompt = 'mb997c'

# -----------------------------------------------------------------------------

class target(object):
  """mb997c- STM32F4 Discovery Board with STM32F407xx SoC"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.device = soc.get_device(self.ui, soc_name)
    self.jlink = jlink.JLink(usb_number, self.device.cpu.name, jlink._JLINKARM_TIF_SWD)


    self.cpu = cortexm.cortexm(self, ui, self.jlink, info['cpu'])
    #self.soc = soc.soc(self.cpu, info)
    #self.mem = mem.mem(self.cpu, self.soc)

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
    """exit the application"""
    self.jlink.jlink_close()
    ui.exit()

# -----------------------------------------------------------------------------
