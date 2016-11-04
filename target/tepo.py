# -----------------------------------------------------------------------------
"""

Teenage Engineering Pocket Operator (EFM32LG890F128)

"""
# -----------------------------------------------------------------------------

import cli
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

# jlink device
default_itf = {
  'name': 'jlink',
  'vid': 0x1366,
  'pid': 0x0101,
  'itf': 0,
}

# -----------------------------------------------------------------------------
# gpio configuration: see -http://hackingthepo.weebly.com/

gpio_cfg = (
  # PA0 lcd (lcd_seg13)
  # PA1 led_col3 (gpio)
  # PA2 lcd (lcd_seg15)
  # PA3 led_col2 (gpio)
  # PA4 lcd (lcd_seg17)
  # PA5 led_row1 (gpio)
  # PA6 led_col1 (gpio)
  # PA7 lcd (lcd_seg35)
  # PA8 lcd (lcd_seg36)
  # PA9 lcd (lcd_seg37)
  # PA10 lcd (lcd_seg38)
  # PA11 lcd (lcd_seg39)
  # PA12 lcd (LCD_BCAP_P) unconnected?
  # PA13 lcd (LCD_BCAP_N) unconnected?
  # PA14 lcd (LCD_BEXT) unconnected?
  # PA15 lcd (lcd_seg12)
  # PB0 lcd (lcd_seg32)
  # PB1 led_col0 (gpio)
  # PB2 lcd (lcd_seg34)
  # PB3 led_row2 (gpio)
  # PB4 lcd (lcd_seg21)
  # PB5 lcd (lcd_seg22)
  # PB6 lcd (lcd_seg23)
  # PB7
  # PB8
  # PB9 key_15 (gpio)
  # PB10 key_11 (gpio)
  # PB11 key_6 (gpio)
  # PB12 key_14 (gpio)
  # PB13
  # PB14
  # PB15 led_row3 (gpio)
  # PC0 led_row0 (gpio)
  # PC1 key_sound (gpio)
  # PC2 key_1 (gpio)
  # PC3 key_5 (gpio)
  # PC4 key_9 (gpio)
  # PC5 key_13 (gpio)
  # PC6 key_16 (gpio)
  # PC7 key_4 (gpio)
  # PC8 key_12 (gpio)
  # PC9 key_play (gpio)
  # PC10 key_8 (gpio)
  # PC11 key_style (gpio)
  # PC12 key_oo (gpio)
  # PC13 codec reset
  # PC14 input common (gpio)
  # PC15
  # PD0 codec sdin (us1_tx, 1)
  # PD1 codec sdout (us1_rx, 1)
  # PD2 codec sclk (us1_clk, 1)
  # PD3 codec lrck (us1_cs, 1)
  # PD4 right pot (adc0_ch4)
  # PD5 left pot (adc0_ch5)
  # PD6 codec sda (i2c0_sda, 1)
  # PD7 codec scl (i2c0_scl, 1)
  # PD8 key_7 (gpio)
  # PD9 lcd (lcd_seg28)
  # PD10 lcd (lcd_seg29)
  # PD11 lcd (lcd_seg30)
  # PD12 lcd (lcd_seg31)
  # PD13 key_10 (gpio)
  # PD14 key_pattern (gpio)
  # PD15 key_2 (gpio)
  # PE0 key_3 (gpio)
  # PE1 key_bpm (gpio)
  # PE2 codec mclk (tim3_cc2, 1)
  # PE3 key_write (gpio)
  # PE4 lcd (lcd_com0)
  # PE5 lcd (lcd_com1)
  # PE6 lcd (lcd_com2)
  # PE7 lcd (lcd_com3)
  # PE8 lcd (lcd_seg4)
  # PE9 lcd (lcd_seg5)
  # PE10 lcd (lcd_seg6)
  # PE11 lcd (lcd_seg7)
  # PE12 lcd (lcd_seg8)
  # PE13 lcd (lcd_seg9)
  # PE14 lcd (lcd_seg10)
  # PE15 lcd (lcd_seg11)
  # PF0 (DBG_SWCLK)
  # PF1 (DBG_SWDIO)
  # PF2 lcd (lcd_seg0)
  # PF3 lcd (lcd_seg1)
  # PF4 lcd (lcd_seg2)
  # PF5 lcd (lcd_seg3)
  # PF6 lcd (lcd_seg24)
  # PF7 lcd (lcd_seg25)
  # PF8 lcd (lcd_seg26)
  # PF9 lcd (lcd_seg27)
  # PF10 not available
  # PF11 not available
  # PF12 not available
  # PF13 not available
  # PF14 not available
  # PF15 not available
)

# -----------------------------------------------------------------------------

class target(object):
  """tepo- Teenage Engineering Pocket Operator with EFM32LG890F128 SoC"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    #self.flash = flash.flash(flash_driver.sdrv(self.device), self.device, self.mem)
    #gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    #self.gpio = gpio.gpio(gpio_drv)
    #self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'PB6', 'PB9'))

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('debugger', self.dbgio.menu, 'debugger functions'),
      ('exit', self.cmd_exit),
      #('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      #('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
      #('i2c', self.i2c.menu, 'i2c functions'),
      ('map', self.device.cmd_map),
      ('mem', self.mem.menu, 'memory functions'),
      #('program', self.flash.cmd_program, flash.help_program),
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
