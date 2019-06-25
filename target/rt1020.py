# -----------------------------------------------------------------------------
"""

MIMXRT-1020-EVK Evaluation Kit (i.MX RT1020)

SoC: NXP PIMXRT1021DAG5A
SDRAM: ISSI IS42S16160J-6TLI
CODEC: Cirrus Logic WM8960G
Ethernet Phy: Microchip KSZ8081

"""
# -----------------------------------------------------------------------------

import cli
import cortexm
import mem
import soc
import vendor.nxp.imxrt as imxrt
import vendor.nxp.firmware as firmware

# -----------------------------------------------------------------------------

soc_name = 'MIMXRT1021DAG5A'
prompt = 'rt1020'

# -----------------------------------------------------------------------------

# cmsis-dap device
default_itf = {
  #'name': 'cmsis-dap',
  'name': 'jlink',
}

# -----------------------------------------------------------------------------

class target:
  """rt1020 - NXP i.MX RT1020 Evaluation Kit"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = imxrt.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.fw = firmware.firmware(self.cpu)

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      ('fw', self.fw.menu, 'firmware functions'),
      ('go', self.cpu.cmd_go),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
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
    """set the command prompt"""
    indicator = ('*', '')[self.dbgio.is_halted()]
    self.ui.cli.set_prompt('%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------
