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
# gpio configuration: see -http://hackingthepo.weebly.com/

gpio_cfg = (
  # PA0 lcd seg 13
  # PA1 led col 3
  # PA2 lcd seg 15
  # PA3 led col 2
  # PA4 lcd seg 17
  # PA5 led row 1
  # PA6 led col 1
  # PA7 lcd seg 35
  # PA8 lcd seg 36
  # PA9 lcd seg 37
  # PA10 lcd seg 38
  # PA11 lcd seg 39
  # PA12
  # PA13
  # PA14
  # PA15 lcd seg 12
  # PB0 lcd seg 32
  # PB1 led col 0
  # PB2 lcd seg 34
  # PB3 led row 2
  # PB4 lcd seg 21
  # PB5 lcd seg 22
  # PB6 lcd seg 23
  # PB7
  # PB8
  # PB9 key 15
  # PB10 key 11
  # PB11 key 6
  # PB12 key 14
  # PB13
  # PB14
  # PB15 led row 3
  # PC0 led row 0
  # PC1 key sound
  # PC2 key 1
  # PC3 key 5
  # PC4 key 9
  # PC5 key 13
  # PC6 key 16
  # PC7 key 4
  # PC8 key 12
  # PC9 key play
  # PC10 key 8
  # PC11 key style
  # PC12 key oo
  # PC13 codec reset
  # PC14 input common
  # PC15
  # PD0 codec sdin (us1_tx_1)
  # PD1 codec sdout (us1_rx_1)
  # PD2 codec sclk (us1_clk_1)
  # PD3 codec lrck (us1_cs_1)
  # PD4 right pot (adc0_ch4)
  # PD5 left pot (adc0_ch5)
  # PD6 codec sda (i2c0_sda_1)
  # PD7 codec scl (i2c0_scl_1)
  # PD8 key 7
  # PD9 lcd seg 28
  # PD10 lcd seg 29
  # PD11 lcd seg 30
  # PD12 lcd seg 31
  # PD13 key 10
  # PD14 key pattern
  # PD15 key 2
  # PE0 key 3
  # PE1 key bpm
  # PE2 codec mclk (tim3_cc2_1)
  # PE3 key write
  # PE4 lcd com 0
  # PE5 lcd com 1
  # PE6 lcd com 2
  # PE7 lcd com 3
  # PE8 lcd seg 4
  # PE9 lcd seg 5
  # PE10 lcd seg 6
  # PE11 lcd seg 7
  # PE12 lcd seg 8
  # PE13 lcd seg 9
  # PE14 lcd seg 10
  # PE15 lcd seg 11
  # PF0
  # PF1
  # PF2 lcd seg 0
  # PF3 lcd seg 1
  # PF4 lcd seg 2
  # PF5 lcd seg 3
  # PF6 lcd seg 24
  # PF7 lcd seg 25
  # PF8 lcd seg 26
  # PF9 lcd seg 27
  # PF10
  # PF11
  # PF12
  # PF13
  # PF14
  # PF15
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
