# -----------------------------------------------------------------------------
"""

STM32F3 Discovery Board (STM32F303xC)

"""
# -----------------------------------------------------------------------------

import cli
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

# built in stlinkv2
default_itf = {
  'name': 'stlink',
  'vid': 0x0483,
  'pid': 0x3748,
  'itf': 1,
}

# -----------------------------------------------------------------------------
# gpio configuration

# pin, mode, pupd, otype, ospeed, name
gpio_cfg = (
  ('PA0', 'i', None, None, None, 'pushbutton SW_PUSH'),
  ('PA5', 'i', None, None, None, 'gyro SPI1_SCK'),
  ('PA6', 'i', None, None, None, 'gyro SPI1_MOSI'),
  ('PA7', 'i', None, None, None, 'gyro SPI1_MISO'),
  ('PA11', 'af14', None, None, None, 'USB_DM'),
  ('PA12', 'af14', None, None, None, 'USB_DP'),
  ('PA13', 'af0', None, None, None, 'TMS/SWDIO'),
  ('PA14', 'af0', None, None, None, 'TCK/SCLK'),
  ('PA15', 'af0', None, None, None, 'TDI'),
  ('PB6', 'i', 'pu', 'pp', 'f', 'compass/accelerometer SCL'),
  ('PB7', 'i', 'pu', 'pp', 'f', 'compass/accelerometer SDA'),
  ('PC14', 'i', None, None, None, 'PC14-OSC32_IN'),
  ('PC15', 'i', None, None, None, 'PC14-OSC32_OUT'),
  ('PE0', 'i', None, None, None, 'gyro MEMS_INT1'),
  ('PE1', 'i', None, None, None, 'gyro MEM_INT2'),
  ('PE2', 'i', None, None, None, 'compass/accelerometer DRDY'),
  ('PE3', 'i', None, None, None, 'gyro CS_I2C/SPI'),
  ('PE4', 'i', None, None, None, 'compass/accelerometer INT1'),
  ('PE5', 'i', None, None, None, 'compass/accelerometer INT2'),
  ('PE8', '0', None, 'pp', 'f', 'LD4 blue'),
  ('PE9', '0', None, 'pp', 'f', 'LD3 red'),
  ('PE10', '0', None, 'pp', 'f', 'LD5 orange'),
  ('PE11', '0', None, 'pp', 'f', 'LD7 green'),
  ('PE12', '0', None, 'pp', 'f', 'LD9 blue'),
  ('PE13', '0', None, 'pp', 'f', 'LD10 red'),
  ('PE14', '0', None, 'pp', 'f', 'LD8 orange'),
  ('PE15', '0', None, 'pp', 'f', 'LD6 green'),
  ('PF0', 'i', None, None, None, 'PF0-OSC_IN'),
  ('PF1', 'i', None, None, None, 'PF1-OSC_OUT'),
)

# -----------------------------------------------------------------------------

class target(object):
  """mb1035b- STM32F3 Discovery Board with STM32F303xC SoC"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.stm32f0xx(self.device), self.device, self.mem)
    gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    self.gpio = gpio.gpio(gpio_drv)
    self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'PB6', 'PB7'))

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
      ('i2c', self.i2c.menu, 'i2c functions'),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      ('program', self.flash.cmd_program, flash.help_program),
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
    indicator = ('*', '')[self.dbgio.is_halted()]
    self.ui.cli.set_prompt('%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------
