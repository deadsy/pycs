# -----------------------------------------------------------------------------
"""

Microchip SAML21 Xplained Pro Evaluation Board (ATSAML21J18A)

"""
# -----------------------------------------------------------------------------

import cli
import cortexm
import mem
import soc
import flash
import gpio
import rtt

import vendor.atmel.atmel as atmel
import vendor.atmel.flash as flash_driver
import vendor.atmel.gpio as gpio_driver

# -----------------------------------------------------------------------------

soc_name = 'ATSAML21J18A'
prompt = 'saml21_xpro'

# -----------------------------------------------------------------------------

# jlink device
default_itf = {
  'name': 'jlink',
  'vid': 0x1366,
  'pid': 0x0101,
  'itf': 0,
}

# -----------------------------------------------------------------------------
# gpio configuration

# None = not configured
# i = input (no internal pull up/down)
# i_pu = input (with internal pull up)
# i_pd = input (with internal pull down)
# o = output (normal drive strength)
# o_s = output (strong drive strength)

# pin, mode, name
gpio_cfg = (
    ('PA00', None, ''),
    ('PA01', None, ''),
    ('PA02', 'i_pu', 'SW0'),
    ('PA03', None, ''),
    ('PA04', None, ''),
    ('PA05', None, ''),
    ('PA06', None, ''),
    ('PA07', None, ''),
    ('PA08', None, ''),
    ('PA09', None, ''),
    ('PA10', None, ''),
    ('PA11', None, ''),
    ('PA12', None, ''),
    ('PA13', None, ''),
    ('PA14', None, ''),
    ('PA15', None, ''),
    ('PA16', None, ''),
    ('PA17', None, ''),
    ('PA18', None, ''),
    ('PA19', None, ''),
    ('PA20', None, ''),
    ('PA21', None, ''),
    ('PA22', None, ''),
    ('PA23', None, ''),
    ('PA24', None, ''),
    ('PA25', None, ''),
    ('PA26', None, ''),
    ('PA27', None, ''),
    ('PA28', None, ''),
    ('PA29', None, ''),
    ('PA30', None, ''),
    ('PA31', None, ''),
    ('PB00', None, ''),
    ('PB01', None, ''),
    ('PB02', None, ''),
    ('PB03', None, ''),
    ('PB04', None, ''),
    ('PB05', None, ''),
    ('PB06', None, ''),
    ('PB07', None, ''),
    ('PB08', None, ''),
    ('PB09', None, ''),
    ('PB10', 'o', 'LED0'),
    ('PB11', None, ''),
    ('PB12', None, ''),
    ('PB13', None, ''),
    ('PB14', None, ''),
    ('PB15', None, ''),
    ('PB16', None, ''),
    ('PB17', None, ''),
    ('PB18', None, ''),
    ('PB19', None, ''),
    ('PB20', None, ''),
    ('PB21', None, ''),
    ('PB22', None, ''),
    ('PB23', None, ''),
    ('PB24', None, ''),
    ('PB25', None, ''),
    ('PB26', None, ''),
    ('PB27', None, ''),
    ('PB28', None, ''),
    ('PB29', None, ''),
    ('PB30', None, ''),
    ('PB31', None, ''),
)

# -----------------------------------------------------------------------------

class target(object):
  """atsaml21_xpro - Microchip SAML21 Xplained Pro Evaluation Board"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = atmel.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.flash(self.device), self.device, self.mem)
    gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    self.gpio = gpio.gpio(gpio_drv)
    # setup the rtt client
    ram = self.device.sram
    self.rtt = rtt.rtt(self.cpu, mem.region('ram', ram.address, ram.size))

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      ('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      ('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      ('program', self.flash.cmd_program, flash.help_program),
      ('regs', self.cmd_regs, soc.help_regs),
      ('rtt', self.rtt.menu, 'rtt client functions'),
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
