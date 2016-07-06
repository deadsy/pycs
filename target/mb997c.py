# -----------------------------------------------------------------------------
"""

STM32F4 Discovery Board (STM32F407xx)

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

import vendor.st.st as vendor
import vendor.st.flash as flash_driver
import vendor.st.gpio as gpio_driver

# -----------------------------------------------------------------------------

soc_name = 'STM32F407xx'
prompt = 'mb997c'

# -----------------------------------------------------------------------------

gpio_cfg = {

  'PA0': ('SW_PUSH',),
  'PA1': ('system_reset',),
  'PA4': ('I2S3_WS',),
  'PA5': ('SPI1_SCK',),
  'PA6': ('SPI1_MISO',),
  'PA7': ('SPI1_MOSI',),
  'PA9': ('VBUS_FS',),
  'PA10': ('OTG_FS_ID',),
  'PA11': ('OTG_FS_DM',),
  'PA12': ('OTG_FS_DP',),
  'PA13': ('SWDIO',),
  'PA14': ('SWCLK',),
  'PB3': ('SWO',),
  'PB6': ('Audio_SCL',),
  'PB9': ('Audio_SDA',),
  'PB10': ('CLK_IN',),
  'PC0': ('OTG_FS_PowerSwitchOn',),
  'PC3': ('PDM_OUT',),
  'PC4': ('codec',),
  'PC7': ('I2S3_MCK',),
  'PC10': ('I2S3_SCK',),
  'PC12': ('I2S3_SD',),
  'PC14': ('osc_in',),
  'PC15': ('osc_out',),
  'PD4': ('Audio_RST',),
  'PD5': ('OTG_FS_OverCurrent',),
  'PD12': ('LED4',),
  'PD13': ('LED3',),
  'PD14': ('LED5',),
  'PD15': ('LED6',),
  'PE0': ('MEMS_INT1',),
  'PE1': ('MEMS_INT2',),
  'PE3': ('CS_I2C/SPI',),
  'PH0': ('ph0_osc_in',),
  'PH1': ('ph1_osc_out',),
}

# -----------------------------------------------------------------------------

class target(object):
  """mb997c- STM32F4 Discovery Board with STM32F407xx SoC"""

  def __init__(self, ui, usb_number):
    self.ui = ui
    self.device = vendor.get_device(self.ui, soc_name)
    self.jlink = jlink.JLink(usb_number, self.device.cpu_info.name, jlink._JLINKARM_TIF_SWD)
    self.cpu = cortexm.cortexm(self, ui, self.jlink, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.sdrv(self.device), self.device, self.mem)
    self.gpio = gpio.gpio(gpio_driver.drv(self.device, gpio_cfg))

    self.menu_root = (
      ('cpu', self.cpu.menu, 'cpu functions'),
      ('da', self.cpu.cmd_disassemble, cortexm.help_disassemble),
      ('exit', self.cmd_exit),
      ('flash', self.flash.menu, 'flash functions'),
      ('go', self.cpu.cmd_go),
      ('gpio', self.gpio.menu, 'gpio functions'),
      ('halt', self.cpu.cmd_halt),
      ('help', self.ui.cmd_help),
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
