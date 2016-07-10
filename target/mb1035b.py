# -----------------------------------------------------------------------------
"""

STM32F3 Discovery Board (STM32F303xC)

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

import vendor.st.st as vendor
import vendor.st.flash as flash_driver
import vendor.st.gpio as gpio_driver
import vendor.st.i2c as i2c_driver

# -----------------------------------------------------------------------------

soc_name = 'STM32F303xC'
prompt = 'mb1035b'

# -----------------------------------------------------------------------------
# gpio configuration

# pin, mode, pupd, otype, ospeed, name
gpio_cfg = (

  ('PA0', 'i', None, None, None, 'SW_PUSH'),

  ('PB6', 'i', 'pu', 'pp', 'f', 'SCL compass/accelerometer'),
  ('PB7', 'i', 'pu', 'pp', 'f', 'SDA compass/accelerometer'),

  ('PE8', '0', None, 'pp', 'f', 'LD4'),
  ('PE9', '0', None, 'pp', 'f', 'LD3'),
  ('PE10', '0', None, 'pp', 'f', 'LD5'),
  ('PE11', '0', None, 'pp', 'f', 'LD7'),
  ('PE12', '0', None, 'pp', 'f', 'LD9'),
  ('PE13', '0', None, 'pp', 'f', 'LD10'),
  ('PE14', '0', None, 'pp', 'f', 'LD8'),
  ('PE15', '0', None, 'pp', 'f', 'LD6'),

)

# -----------------------------------------------------------------------------

class target(object):
  """mb1035b- STM32F3 Discovery Board with STM32F303xC SoC"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.device = vendor.get_device(self.ui, soc_name)
    self.jlink = jlink.JLink(usb_number, self.device.cpu_info.name, jlink._JLINKARM_TIF_SWD)
    self.cpu = cortexm.cortexm(self, ui, self.jlink, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.pdrv(self.device), self.device, self.mem)
    gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    self.gpio = gpio.gpio(gpio_drv)
    self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'PB6', 'PB7'))

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('exit', self.cmd_exit),
      ('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      ('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('i2c', self.i2c.menu, 'i2c functions'),
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
