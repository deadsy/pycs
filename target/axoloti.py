# -----------------------------------------------------------------------------
"""

Axoloti Synth Board (STM32F427xx)

http://www.axoloti.com/

CPU: STM32F427IGH6 (G=1MiB flash)
Codec: ADAU1361BCPZ (96kHz, 24 bit stereo codec)
SDRAM: AS4C4M16SA-7BCN (4Mx16bit SDRAM)

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

soc_name = 'STM32F427xG'
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
  ('PA0', 'i', 'pd', None, None, 'tp37'), # ADC1_IN0
  ('PA1', 'i', 'pd', None, None, 'tp38'), # ADC1_IN1
  ('PA2', 'i', 'pd', None, None, 'tp39'), # ADC1_IN2
  ('PA3', 'i', 'pd', None, None, 'tp40'), # ADC1_IN3
  ('PA4', 'i', 'pd', None, None, 'tp41'), # ADC1_IN4/DAC_OUT1/SPI_NSS
  ('PA5', 'i', 'pd', None, None, 'tp42'), # ADC1_IN5/DAC_OUT2/SPI_SCK
  ('PA6', 'i', 'pd', None, None, 'tp43'), # ADC1_IN6/SPI_MISO
  ('PA7', 'i', 'pd', None, None, 'tp44'), # ADC1_IN7/SPI_MOSI
  ('PA8', 'af0', None, None, None, 'codec_mclk, x4_2'),

  ('PA10', 'i', 'pd', None, None, 's2'),
  ('PA11', 'af10', None, None, None, 'fs_dm'),
  ('PA12', 'af10', None, None, None, 'fs_dp'),
  ('PA13', 'af0', None, None, None, 'swdio'), # swd
  ('PA14', 'af0', None, None, None, 'swclk'), # swd
  ('PA15', 'i', 'pd', None, None, 'x3_6'),

  ('PB0', 'i', 'pd', None, None, 'tp45'), # ADC1_IN8
  ('PB1', 'i', 'pd', None, None, 'tp46'), # ADC1_IN9

  ('PB3', 'i', 'pd', None, None, 'x3_5'),
  ('PB4', 'i', 'pd', None, None, 'x3_7'),
  ('PB5', 'i', 'pd', None, None, 'boot0'), # same signal as the boot0 pin
  ('PB6', 'i', 'pd', None, None, 'tp47'), # UART_TX
  ('PB7', 'i', 'pd', None, None, 'tp48'), # UART_RX
  ('PB8', 'i', 'pd', None, None, 'tp49'), # I2C1_SCL
  ('PB9', 'i', 'pd', None, None, 'tp50'), # I2C1_SDA
  ('PB10', 'i', 'pd', None, None, 'x3_2, x4_5'),

  ('PB14', 'af12', None, None, None, 'hs_dm'), # usb1
  ('PB15', 'af12', None, None, None, 'hs_dp'), # usb1

  ('PC0', 'i', 'pd', None, None, 'tp51'), # ADC1_IN10
  ('PC1', 'i', 'pd', None, None, 'tp52'), # ADC1_IN11
  ('PC2', 'i', 'pd', None, None, 'tp53'), # ADC1_IN12
  ('PC3', 'i', 'pd', None, None, 'tp54'), # ADC1_IN13
  ('PC4', 'i', 'pd', None, None, 'tp55'), # ADC1_IN14
  ('PC5', 'i', 'pd', None, None, 'tp56'), # ADC1_IN15
  ('PC6', '0', None, 'pp', 'f', 'led_red'),

  ('PC8', 'af12', None, None, None, 'sdio_d0'),
  ('PC9', 'af12', None, None, None, 'sdio_d1'),
  ('PC10', 'af12', None, None, None, 'sdio_d2'),
  ('PC11', 'af12', None, None, None, 'sdio_d3'),
  ('PC12', 'af12', None, None, None, 'sdio_ck'),

  ('PD0', 'af12', None, None, None, 'sdram_d2'),
  ('PD1', 'af12', None, None, None, 'sdram_d3'),
  ('PD2', 'af12', None, None, None, 'sdio_cmd'),

  ('PD6', 'i', 'pd', None, None, 'x3_4'),
  ('PD7', '1', None, 'pp', 'f', 'usb_enable'), # active low USB1 power enable
  ('PD8', 'af12', None, None, None, 'sdram_d13'),
  ('PD9', 'af12', None, None, None, 'sdram_d14'),
  ('PD10', 'af12', None, None, None, 'sdram_d15'),

  ('PD13', 'i', 'pd', None, None, 'sdio_cd1'), # sdio card detect 1
  ('PD14', 'af12', None, None, None, 'sdram_d0'),
  ('PD15', 'af12', None, None, None, 'sdram_d1'),

  ('PE0', 'af12', None, None, None, 'sdram_ldqm'),
  ('PE1', 'af12', None, None, None, 'sdram_udqm'),

  ('PE3', 'af6', None, None, None, 'Codec ADC_SDATA/GPIO1'),
  ('PE4', 'af6', None, None, None, 'codec_lrclk, x4-4'),
  ('PE5', 'af6', None, None, None, 'codec_bclk, x4-3'),
  ('PE6', 'af6', None, None, None, 'Codec DAC_SDATA/GPIO0'),

  ('PE7', 'af12', None, None, None, 'sdram_d4'),
  ('PE8', 'af12', None, None, None, 'sdram_d5'),
  ('PE9', 'af12', None, None, None, 'sdram_d6'),
  ('PE10', 'af12', None, None, None, 'sdram_d7'),
  ('PE11', 'af12', None, None, None, 'sdram_d8'),
  ('PE12', 'af12', None, None, None, 'sdram_d9'),
  ('PE13', 'af12', None, None, None, 'sdram_d10'),
  ('PE14', 'af12', None, None, None, 'sdram_d11'),
  ('PE15', 'af12', None, None, None, 'sdram_d12'),

  ('PF0', 'af12', None, None, None, 'sdram_a0'),
  ('PF1', 'af12', None, None, None, 'sdram_a1'),
  ('PF2', 'af12', None, None, None, 'sdram_a2'),
  ('PF3', 'af12', None, None, None, 'sdram_a3'),
  ('PF4', 'af12', None, None, None, 'sdram_a4'),
  ('PF5', 'af12', None, None, None, 'sdram_a5'),
  ('PF10', 'an', None, None, None, 'power_monitor'), # ADC3_IN8
  ('PF11', 'af12', None, None, None, 'sdram_ras'),
  ('PF12', 'af12', None, None, None, 'sdram_a6'),
  ('PF13', 'af12', None, None, None, 'sdram_a7'),
  ('PF14', 'af12', None, None, None, 'sdram_a8'),
  ('PF15', 'af12', None, None, None, 'sdram_a9'),

  ('PG0', 'af12', None, None, None, 'sdram_a10'),
  ('PG1', 'af12', None, None, None, 'sdram_a11'),
  ('PG2', 'af12', None, None, None, 'sdram_a12'),

  ('PG4', 'af12', None, None, None, 'sdram_ba0'),
  ('PG5', 'af12', None, None, None, 'sdram_ba1'),
  ('PG6', '0', None, 'pp', 'f', 'led_green'),

  ('PG8', 'af12', None, None, None, 'sdram_clk'),
  ('PG9', 'af8', None, None, None, 'midi_in'),

  ('PG13', 'i', 'pu', None, None, 'usb_flag'), # fault report on USB1
  ('PG14', 'af8', None, None, None, 'midi_out'),
  ('PG15', 'af12', None, None, None, 'sdram_cas'),

  ('PH2', 'af12', None, None, None, 'sdram_cke'),
  ('PH3', 'af12', None, None, None, 'sdram_cs0'),

  ('PH5', 'af12', None, None, None, 'sdram_we'),

  ('PH7', 'i', 'pu', 'pp', 'f', 'codec_scl'), # normally af4
  ('PH8', 'i', 'pu', 'pp', 'f', 'codec_sda'), # normally af4
)

# -----------------------------------------------------------------------------

class target(object):
  """axoloti- Axoloti Synth Board with STM32F427xx SoC"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    # add the 8MiB SDRAM
    self.device.insert(soc.make_peripheral('sdram', 0xc0000000, 8 << 20, None, 'external sdram'))
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
