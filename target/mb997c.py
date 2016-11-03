# -----------------------------------------------------------------------------
"""

STM32F4 Discovery Board (STM32F407xx)

"""
# -----------------------------------------------------------------------------

import cli
import cortexm
import mem
import soc
import flash
import gpio
import i2c
import rtt

import vendor.st.st as vendor
import vendor.st.flash as flash_driver
import vendor.st.gpio as gpio_driver
import vendor.st.i2c as i2c_driver

import drivers.cs4x as dac

# -----------------------------------------------------------------------------

soc_name = 'STM32F407xx'
prompt = 'mb997c'

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
  ('PA0', 'i', None, None, None, 'SW_PUSH'),
  ('PA1', 'i', None, None, None, 'system_reset'),
  ('PA4', 'i', None, None, None, 'I2S3_WS'),
  ('PA5', 'i', None, None, None, 'SPI1_SCK'),
  ('PA6', 'i', None, None, None, 'SPI1_MISO'),
  ('PA7', 'i', None, None, None, 'SPI1_MOSI'),
  ('PA9', 'i', None, None, None, 'VBUS_FS'),
  ('PA10', 'i', None, None, None, 'OTG_FS_ID'),
  ('PA11', 'i', None, None, None, 'OTG_FS_DM'),
  ('PA12', 'i', None, None, None, 'OTG_FS_DP'),
  ('PA13', 'af0', None, None, None, 'SWDIO'),
  ('PA14', 'af0', None, None, None, 'SWCLK'),

  ('PB3', 'af0', None, None, None, 'SWO'),
  ('PB6', 'i', 'pu', 'pp', 'f', 'Audio_SCL'),
  ('PB9', 'i', 'pu', 'pp', 'f', 'Audio_SDA'),
  ('PB10', 'i', None, None, None, 'CLK_IN'),

  ('PC0', 'i', None, None, None, 'OTG_FS_PowerSwitchOn'),
  ('PC3', 'i', None, None, None, 'PDM_OUT'),
  ('PC4', 'i', None, None, None, 'codec'),
  ('PC7', 'i', None, None, None, 'I2S3_MCK'),
  ('PC10', 'i', None, None, None, 'I2S3_SCK'),
  ('PC12', 'i', None, None, None, 'I2S3_SD'),
  ('PC14', 'i', None, None, None, 'osc_in'),
  ('PC15', 'i', None, None, None, 'osc_out'),

  ('PD4', '1', None, 'pp', 'f', 'Audio_RST'),
  ('PD5', 'i', None, None, None, 'OTG_FS_OverCurrent'),
  ('PD12', '0', None, 'pp', 'f', 'LED4'),
  ('PD13', '0', None, 'pp', 'f', 'LED3'),
  ('PD14', '0', None, 'pp', 'f', 'LED5'),
  ('PD15', '0', None, 'pp', 'f', 'LED6'),

  ('PE0', 'i', None, None, None, 'MEMS_INT1'),
  ('PE1', 'i', None, None, None, 'MEMS_INT2'),
  ('PE3', 'i', None, None, None, 'CS_I2C/SPI'),

  ('PH0', 'i', None, None, None, 'ph0_osc_in'),
  ('PH1', 'i', None, None, None, 'ph1_osc_out'),
)

# -----------------------------------------------------------------------------

class target(object):
  """mb997c- STM32F4 Discovery Board with STM32F407xx SoC"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.sdrv(self.device), self.device, self.mem)
    gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    self.gpio = gpio.gpio(gpio_drv)
    self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'PB6', 'PB9'))
    self.dac = dac.cs43l22(self.i2c, 0x94, self.dac_reset)
    # setup the rtt client
    ram = self.device.sram
    self.rtt = rtt.rtt(self.cpu, mem.region('ram', ram.address, ram.size))

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('dac', self.dac.menu, 'dac functions'),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      ('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      ('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history),
      ('i2c', self.i2c.menu, 'i2c functions'),
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

  def dac_reset(self, x):
    """control the dac reset line"""
    self.gpio.wr_bit('GPIOD', 4, x)

# -----------------------------------------------------------------------------
