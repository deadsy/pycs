# -----------------------------------------------------------------------------
"""

Target file for nRF52dk

"""
# -----------------------------------------------------------------------------

import conio
import cli
import jlink
import cortexm
import mem
import soc
import flash

import vendor.nordic.nordic as vendor
import vendor.nordic.flash as flash_driver

# -----------------------------------------------------------------------------

soc_name = 'nRF52832'
prompt = 'nRF52dk'

# -----------------------------------------------------------------------------
"""

Notes:

1) The GPIO pin usage depends on if a shield is plugged in.
If there is no shield the GPIOs are used directly for LEDs and buttons.
If there is a shield the GPIOs are used for the headers (ala arduino), and
the LEDs and buttons are accessed via an I2C port expander.

2) The UART pins aren't specified by the target hardware, but for convenience
I'm setting them per the default pin selects in the SDK.

"""

gpio_cfg = {

#  'P0.01': ('',),
#  'P0.02': ('',),
#  'P0.03': ('',),
#  'P0.04': ('',),
  'P0.05': ('UART_RTS',),
  'P0.06': ('UART_TX',),
  'P0.07': ('UART_CTS',),
  'P0.08': ('UART_RX',),
#  'P0.09': ('',),
#  'P0.10': ('',),
#  'P0.11': ('',),
#  'P0.12': ('',),
  'P0.13': ('BUTTON_1 (no shield)',),
  'P0.14': ('BUTTON_2 (no shield)',),
  'P0.15': ('BUTTON_3 (no shield)',),
  'P0.16': ('BUTTON_4 (no shield)',),
  'P0.17': ('LED_1 (no shield) INT_EXT (shield)',),
  'P0.18': ('LED_2 (no shield)',),
  'P0.19': ('LED_3 (no shield)',),
  'P0.20': ('LED_4 (no shield)',),
#  'P0.21': ('',),
#  'P0.22': ('',),
#  'P0.23': ('',),
#  'P0.24': ('',),
#  'P0.25': ('',),
  'P0.26': ('SDA_EXT (shield)',),
  'P0.27': ('SCL_EXT (shield)',),
#  'P0.28': ('',),
#  'P0.29': ('',),
#  'P0.30': ('',),
#  'P0.31': ('',),
}

# -----------------------------------------------------------------------------

class target(object):
  """nRF52dk- Nordic nRF52 Developer's Kit"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.device = vendor.get_device(self.ui, soc_name)
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
    """exit application"""
    self.jlink.jlink_close()
    ui.exit()

# -----------------------------------------------------------------------------
