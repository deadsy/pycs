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
import vendor.st.st as st
import soc

# -----------------------------------------------------------------------------

soc_name = 'STM32F407xx'
prompt = 'mb997c'

# -----------------------------------------------------------------------------

class target(object):
  """mb997c- STM32F4 Discovery Board with STM32F407xx SoC"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.device = st.get_device(self.ui, soc_name)
    self.jlink = jlink.JLink(usb_number, self.device.cpu_info.name, jlink._JLINKARM_TIF_SWD)
    self.cpu = cortexm.cortexm(self, ui, self.jlink, self.device.cpu_info)
    self.device.set_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)

    #self.soc = soc.soc(self.cpu, info)

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('exit', self.cmd_exit),
      ('go', self.cpu.cmd_go),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('jlink', self.jlink.cmd_jlink),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      ('regs', self.cmd_regs, soc.help_regs),
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
