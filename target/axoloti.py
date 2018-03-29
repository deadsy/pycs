# -----------------------------------------------------------------------------
"""

Axoloti Synth Board (STM32F427xx)

http://www.axoloti.com/

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
import gdb

import vendor.st.st as vendor
import vendor.st.flash as flash_driver
import vendor.st.gpio as gpio_driver
import vendor.st.i2c as i2c_driver

# -----------------------------------------------------------------------------

soc_name = 'STM32F427xx'
prompt = 'axoloti'

# -----------------------------------------------------------------------------

# using a 3rd party stlinkv2 dongle
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
  #('PA0', 'i', None, None, None, 'ADC1_IN0'),
  #('PA1', 'i', None, None, None, 'ADC1_IN1'),
  #('PA2', 'i', None, None, None, 'ADC1_IN2'),
  #('PA3', 'i', None, None, None, 'ADC1_IN3'),
  #('PA4', 'i', None, None, None, 'ADC1_IN4/DAC_OUT1/SPI_NSS'),
  #('PA5', 'i', None, None, None, 'ADC1_IN5/DAC_OUT2/SPI_SCK'),
  #('PA6', 'i', None, None, None, 'ADC1_IN6/SPI_MISO'),
  #('PA7', 'i', None, None, None, 'ADC1_IN7/SPI_MOSI'),

  ('PA8', 'i', None, None, None, 'I2S_MCLK'), # codec
  ('PA10', 'i', None, None, None, 'SW_PUSH'),
  ('PA13', 'af0', None, None, None, 'SWDIO'), # swd
  ('PA14', 'af0', None, None, None, 'SWCLK'), # swd

  #('PB0', 'i', None, None, None, 'ADC1_IN8'),
  #('PB1', 'i', None, None, None, 'ADC1_IN9'),
  #('PB6', 'i', None, None, None, 'UART_TX'),
  #('PB7', 'i', None, None, None, 'UART_RX'),
  #('PB8', 'i', None, None, None, 'I2C1_SCL'),
  #('PB9', 'i', None, None, None, 'I2C1_SDA'),

  #('PC0', 'i', None, None, None, 'ADC1_IN10'),
  #('PC1', 'i', None, None, None, 'ADC1_IN11'),
  #('PC2', 'i', None, None, None, 'ADC1_IN12'),
  #('PC3', 'i', None, None, None, 'ADC1_IN13'),
  #('PC4', 'i', None, None, None, 'ADC1_IN14'),
  #('PC5', 'i', None, None, None, 'ADC1_IN15'),

  ('PC6', '0', None, 'pp', 'f', 'LED_RED'),
  ('PC8', 'i', None, None, None, 'SDIO_D0'), # sdio
  ('PC9', 'i', None, None, None, 'SDIO_D1'), # sdio
  ('PC10', 'i', None, None, None, 'SDIO_D2'), # sdio
  ('PC11', 'i', None, None, None, 'SDIO_D3'), # sdio
  ('PC12', 'i', None, None, None, 'SDIO_CK'), # sdio

  ('PD2', 'i', None, None, None, 'SDIO_CMD'), # sdio

  ('PE3', 'i', None, None, None, 'I2S_SD2'), # codec
  ('PE4', 'i', None, None, None, 'I2S_LRCLK'), # codec
  ('PE5', 'i', None, None, None, 'I2S_BCLK'), # codec
  ('PE6', 'i', None, None, None, 'I2S_SD1'), # codec

  ('PF10', 'i', None, None, None, 'ADC3_IN8'), # power monitor

  ('PG6', '0', None, 'pp', 'f', 'LED_GREEN'),
  ('PG9', 'i', None, None, None, 'UART_RX'), # midi
  ('PG14', 'i', None, None, None, 'UART_TX'), # midi

  ('PH7', 'i', None, None, None, 'I2C_SCL'), # codec
  ('PH8', 'i', None, None, None, 'I2C_SDA'), # codec
)

# -----------------------------------------------------------------------------

class target(object):
  """axoloti- Axoloti Synth Board with STM32F427xx SoC"""

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
    self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'PH7', 'PH8'))
    # setup the rtt client
    ram = self.device.sram
    self.rtt = rtt.rtt(self.cpu, mem.region('ram', ram.address, ram.size))
    # setup the gdb server
    self.gdb = gdb.gdb(self.cpu)

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      ('flash', self.flash.menu, 'flash functions'),
      ('gdb', self.gdb.run),
      ('go', self.cpu.cmd_go),
      ('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
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

# -----------------------------------------------------------------------------
