# -----------------------------------------------------------------------------
"""

EFM32 Leopard Gecko Starter Kit (EFM32LG990F256)

"""
# -----------------------------------------------------------------------------

import conio
import cli
import cortexm
import mem
import soc
import flash
import gpio
import i2c
import rtt

import vendor.silabs.silabs as vendor
#import vendor.silabs.flash as flash_driver
import vendor.silabs.gpio as gpio_driver
#import vendor.silabs.i2c as i2c_driver

# -----------------------------------------------------------------------------

soc_name = 'EFM32LG990F256'
prompt = 'efm32lg'

# -----------------------------------------------------------------------------

# built in jlink
default_itf = {
  'name': 'jlink',
  'vid': 0x1366,
  'pid': 0x0101,
  'itf': 1,
}

# -----------------------------------------------------------------------------
# gpio configuration

# pin, ..., name
gpio_cfg = (
)

# -----------------------------------------------------------------------------

class target(object):
  """efm32lg- Silabs EFM32LG Starter Kit"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    #self.flash = flash.flash(flash_driver.flash(self.device), self.device, self.mem)
    gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    self.gpio = gpio.gpio(gpio_drv)
    #self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'P0.27', 'P0.26'))
    # setup the rtt client
    ram = self.device.sram
    self.rtt = rtt.rtt(self.cpu, mem.region('ram', ram.address, ram.size))

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      #('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      ('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      #('i2c', self.i2c.menu, 'i2c functions'),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      #('program', self.flash.cmd_program, flash.help_program),
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
    self.ui.cli.set_prompt('\n%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------
