# -----------------------------------------------------------------------------
"""

EFM32 Leopard Gecko Starter Kit (EFM32LG990F256)

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

  ('PA0', 'lcd_seg13'),
  ('PA1', 'lcd_seg14'),
  ('PA2', 'lcd_seg15'),
  ('PA3', 'lcd_seg16'),
  ('PA4', 'lcd_seg17'),
  ('PA5', 'lcd_seg18'),
  ('PA6', 'lcd_seg19'),
  ('PA7', 'lcd_seg35'),
  ('PA8', 'lcd_seg36'),
  ('PA9', 'lcd_seg37'),
  ('PA10', 'lcd_seg38'),
  ('PA11', 'lcd_seg39'),
  ('PA12', 'lcd_bcap_b'),
  ('PA13', 'lcd_bcap_n'),
  ('PA14', 'lcd_bext'),
  ('PA15', 'lcd_seg12'),
  ('PB0', 'lcd_seg32'),
  ('PB1', 'lcd_seg33'),
  ('PB2', 'lcd_seg34'),
  ('PB3', 'lcd_com4'),
  ('PB4', 'lcd_com5'),
  ('PB5', 'lcd_com6'),
  ('PB6', 'lcd_com7'),
  ('PB7', 'lfxtl_p'),
  ('PB8', 'lfxtl_n'),
  ('PB9', 'uif_pb0'),
  ('PB10', 'uif_pb1'),
  ('PB11', 'dac0_ch0/exp_header8'),
  ('PB12', 'dac0_ch1/exp_header10'),
  ('PB13', 'hfxtl_p'),
  ('PB14', 'hfxtl_n'),
  ('PB15', 'nand_pwr_en'),
  ('PC0', 'exp_header0'),
  ('PC1', 'nand_ale'),
  ('PC2', 'nand_cle'),
  ('PC3', 'exp_header2'),
  ('PC4', 'exp_header4'),
  ('PC5', 'exp_header6'),
  ('PC6', 'acmp0_ch6/exp_header12'),
  ('PC7', 'acmp0_ch7'),
  ('PC8', 'uif_touch0'),
  ('PC9', 'uif_touch1'),
  ('PC10', 'uif_touch2'),
  ('PC11', 'uif_touch3'),
  #('PC12', ''),
  #('PC13', ''),
  #('PC14', ''),
  #('PC15', ''),
  ('PD0', 'exp_header1'),
  ('PD1', 'exp_header3'),
  ('PD2', 'exp_header4'),
  ('PD3', 'opamp_n2'),
  ('PD4', 'opamp_p2'),
  ('PD5', 'opamp_out2'),
  ('PD6', 'exp_header13/les_light_excite'),
  ('PD7', 'exp_header14'),
  ('PD8', 'bu_vin'),
  ('PD9', 'lcd_seg28'),
  ('PD10', 'lcd_seg29'),
  ('PD11', 'lcd_seg30'),
  ('PD12', 'lcd_seg31'),
  ('PD13', 'nand_wp#'),
  ('PD14', 'nand_ce#'),
  ('PD15', 'nand_r/b#'),
  ('PE0', 'uart0_tx#1'),
  ('PE1', 'uart0_rx#1'),
  ('PE2', 'uif_led0'),
  ('PE3', 'uif_led1'),
  ('PE4', 'lcd_com0'),
  ('PE5', 'lcd_com1'),
  ('PE6', 'lcd_com2'),
  ('PE7', 'lcd_com3'),
  ('PE8', 'nand_io0'),
  ('PE9', 'nand_io1'),
  ('PE10', 'nand_io2'),
  ('PE11', 'nand_io3'),
  ('PE12', 'nand_io4'),
  ('PE13', 'nand_io5'),
  ('PE14', 'nand_io6'),
  ('PE15', 'nand_io7'),
  ('PF0', 'dbg_swclk'),
  ('PF1', 'dbg_swdio'),
  ('PF2', 'dbg_swo'),
  #('PF3', ''),
  #('PF4', ''),
  ('PF5', 'efm_usb_vbusen'),
  ('PF6', 'efm_usb_oc_fault'),
  ('PF7', 'efm_bc_en'),
  ('PF8', 'nand_we#'),
  ('PF9', 'nand_re#'),
  ('PF10', 'efm_usb_dm'),
  ('PF11', 'efm_usb_dp'),
  ('PF12', 'efm_usb_id'),
  #('PF13', ''),
  #('PF14', ''),
  #('PF15', ''),
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
      ('history', self.ui.cmd_history, cli.history_help),
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
    self.ui.cli.set_prompt('%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------
