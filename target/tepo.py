# -----------------------------------------------------------------------------
"""

Teenage Engineering Pocket Operator (EFM32LG890F128)

"""
# -----------------------------------------------------------------------------

import conio
import cli
import jlink
import cortexm
import mem
import soc
import flash
import gpio
import i2c

import vendor.silabs.silabs as vendor
#import vendor.silabs.flash as flash_driver
#import vendor.silabs.gpio as gpio_driver
#import vendor.silabs.i2c as i2c_driver

# -----------------------------------------------------------------------------

soc_name = 'EFM32LG890F128'
prompt = 'tepo'

# -----------------------------------------------------------------------------
# gpio configuration

gpio_cfg = (

  # PA0
  # PA1
  # PA2
  # PA3
  # PA4
  # PA5
  # PA6
  # PA7
  # PA8
  # PA9
  # PA10
  # PA11
  # PA12
  # PA13
  # PA14
  # PA15

)

# -----------------------------------------------------------------------------

class target(object):
  """tepo- Teenage Engineering Pocket Operator with EFM32LG890F128 SoC"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.device = vendor.get_device(self.ui, soc_name)
    self.jlink = jlink.JLink(usb_number, self.device.cpu_info.name, jlink._JLINKARM_TIF_SWD)
    self.cpu = cortexm.cortexm(self, ui, self.jlink, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    #self.flash = flash.flash(flash_driver.sdrv(self.device), self.device, self.mem)
    #gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    #self.gpio = gpio.gpio(gpio_drv)
    #self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'PB6', 'PB9'))

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('exit', self.cmd_exit),
      #('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      #('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      #('i2c', self.i2c.menu, 'i2c functions'),
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
