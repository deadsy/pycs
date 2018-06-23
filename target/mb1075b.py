# -----------------------------------------------------------------------------
"""

STM32F4 Discovery Board (STM32F429xI)

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

# -----------------------------------------------------------------------------

soc_name = 'STM32F429xI'
prompt = 'mb1075b'

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
  ('PA1', 'i', None, None, None, 'mems MEMS_INT1'),
  ('PA2', 'i', None, None, None, 'mems MEMS_INT2'),
  ('PA3', 'af14', None, None, None, 'lcd B5'),
  ('PA4', 'af14', None, None, None, 'lcd VSYNC'),
  ('PA6', 'af14', None, None, None, 'lcd G2'),
  ('PA7', 'i', None, None, None, 'acp/rf ACP_RST'),
  ('PA8', 'i', 'pu', 'pp', 'f', 'i2c I2C3_SCL'),
  ('PA11', 'af14', None, None, None, 'lcd R4'),
  ('PA12', 'af14', None, None, None, 'lcd R5'),
  ('PA15', 'af0', None, None, None, 'touchscreen TP_INT1'),
  ('PB0', 'af9', None, None, None, 'lcd R3'),
  ('PB1', 'af9', None, None, None, 'lcd R6'),
  ('PB5', 'af12', None, None, None, 'sdram SDCKE1'),
  ('PB6', 'af12', None, None, None, 'sdram SDNE1'),
  ('PB8', 'af14', None, None, None, 'lcd B6'),
  ('PB9', 'af14', None, None, None, 'lcd B7'),
  ('PB10', 'af14', None, None, None, 'lcd G4'),
  ('PB11', 'af14', None, None, None, 'lcd G5'),
  ('PB12', 'i', None, None, None, 'usb OTG_FS_ID'),
  ('PB13', 'i', None, None, None, 'usb VBUS_FS'),
  ('PB14', 'i', None, None, None, 'usb OTG_FS_DM'),
  ('PB15', 'i', None, None, None, 'usb OTG_FS_DP'),
  ('PC0', 'af12', None, None, None, 'sdram SDNWE'),
  ('PC1', 'i', None, None, None, 'mems NCS_MEMS_SPI'),
  ('PC2', 'i', None, None, None, 'lcd CSX'),
  ('PC4', 'i', None, None, None, 'usb OTG_FS_PSO'),
  ('PC5', 'i', None, None, None, 'usb OTG_FS_OC'),
  ('PC6', 'af14', None, None, None, 'lcd HSYNC'),
  ('PC7', 'af14', None, None, None, 'lcd G6'),
  ('PC9', 'i', 'pu', 'pp', 'f', 'i2c I2C3_SDA'),
  ('PC10', 'af14', None, None, None, 'lcd R2'),
  ('PC14', 'i', None, None, None, 'PC14-OSC32_IN'),
  ('PC15', 'i', None, None, None, 'PC15-OSC32_OUT'),
  ('PD0', 'af12', None, None, None, 'sdram D2'),
  ('PD1', 'af12', None, None, None, 'sdram D3'),
  ('PD2', 'i', None, None, None, 'lcd IM0'),
  ('PD3', 'af14', None, None, None, 'lcd G7'),
  ('PD4', 'i', None, None, None, 'lcd IM1'),
  ('PD5', 'i', None, None, None, 'lcd IM2'),
  ('PD6', 'af14', None, None, None, 'lcd B2'),
  ('PD7', 'i', None, None, None, 'lcd IM3'),
  ('PD8', 'af12', None, None, None, 'sdram D13'),
  ('PD9', 'af12', None, None, None, 'sdram D14'),
  ('PD10', 'af12', None, None, None, 'sdram D15'),
  ('PD11', 'i', None, None, None, 'lcd TE'),
  ('PD12', 'i', None, None, None, 'lcd RDX'),
  ('PD13', 'i', None, None, None, 'lcd WRX_DCX'),
  ('PD14', 'af12', None, None, None, 'sdram D0'),
  ('PD15', 'af12', None, None, None, 'sdram D1'),
  ('PE0', 'af12', None, None, None, 'sdram NBL0'),
  ('PE1', 'af12', None, None, None, 'sdram NBL1'),
  ('PE7', 'af12', None, None, None, 'sdram D4'),
  ('PE8', 'af12', None, None, None, 'sdram D5'),
  ('PE9', 'af12', None, None, None, 'sdram D6'),
  ('PE10', 'af12', None, None, None, 'sdram D7'),
  ('PE11', 'af12', None, None, None, 'sdram D8'),
  ('PE12', 'af12', None, None, None, 'sdram D9'),
  ('PE13', 'af12', None, None, None, 'sdram D10'),
  ('PE14', 'af12', None, None, None, 'sdram D11'),
  ('PE15', 'af12', None, None, None, 'sdram D12'),
  ('PF0', 'af12', None, None, None, 'sdram A0'),
  ('PF1', 'af12', None, None, None, 'sdram A1'),
  ('PF2', 'af12', None, None, None, 'sdram A2'),
  ('PF3', 'af12', None, None, None, 'sdram A3'),
  ('PF4', 'af12', None, None, None, 'sdram A4'),
  ('PF5', 'af12', None, None, None, 'sdram A5'),
  ('PF7', 'af5', None, None, None, 'mems SPI5_SCK, lcd DCX_SCL'),
  ('PF8', 'af5', None, None, None, 'mems SPI5_MISO'),
  ('PF9', 'af5', None, None, None, 'mems SPI5_MOSI, lcd SDA'),
  ('PF10', 'af14', None, None, None, 'lcd ENABLE'),
  ('PF11', 'af12', None, None, None, 'sdram SDNRAS'),
  ('PF12', 'af12', None, None, None, 'sdram A6'),
  ('PF13', 'af12', None, None, None, 'sdram A7'),
  ('PF14', 'af12', None, None, None, 'sdram A8'),
  ('PF15', 'af12', None, None, None, 'sdram A9'),
  ('PG0', 'af12', None, None, None, 'sdram A10'),
  ('PG1', 'af12', None, None, None, 'sdram A11'),
  ('PG4', 'af12', None, None, None, 'sdram BA0'),
  ('PG5', 'af12', None, None, None, 'sdram BA1'),
  ('PG6', 'af14', None, None, None, 'lcd R7'),
  ('PG7', 'af14', None, None, None, 'lcd DOTCLK'),
  ('PG8', 'af12', None, None, None, 'sdram SDCLK'),
  ('PG10', 'af9', None, None, None, 'lcd G3'),
  ('PG11', 'af14', None, None, None, 'lcd B3'),
  ('PG12', 'af9', None, None, None, 'lcd B4'),
  ('PG13', '0', None, 'pp', 'f', 'led LD3 green'),
  ('PG14', '0', None, 'pp', 'f', 'led LD4 red'),
  ('PG15', 'af12', None, None, None, 'sdram SDNCAS'),
  ('PH0', 'i', None, None, None, 'PH0-OSC_IN'),
  ('PH1', 'i', None, None, None, 'PH1-OSC_OUT'),
)

# -----------------------------------------------------------------------------

class target(object):
  """mb1075b- STM32F4 Discovery Board with STM32F429I SoC"""

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
    self.i2c = i2c.i2c(i2c_driver.bitbang(gpio_drv, 'PA8', 'PC9'))
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
