# -----------------------------------------------------------------------------
"""

Nucleo-L432KC (STM32L432KC)

"""
# -----------------------------------------------------------------------------

import conio
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

soc_name = 'STM32L432KC'
prompt = 'nucleo-l432kc'

# -----------------------------------------------------------------------------

# built in stlinkv2
default_itf = {
  'name': 'stlink',
  'vid': 0x0483,
  'pid': 0x374B,
  'itf': 1,
}

# -----------------------------------------------------------------------------

# pin, mode, pupd, otype, ospeed, name
gpio_cfg = (
    ('PA0', 'i', None, None, None, 'CN4.12'),
    ('PA1', 'i', None, None, None, 'CN4.11'),
    ('PA2', 'i', None, None, None, 'CN4.5/VCP_TX'),
    ('PA3', 'i', None, None, None, 'CN4.10'),
    ('PA4', 'i', None, None, None, 'CN4.9'),
    ('PA5', 'i', None, None, None, 'CN4.8'),
    ('PA6', 'i', None, None, None, 'CN4.7'),
    ('PA7', 'i', None, None, None, 'CN4.6'),
    ('PA8', 'i', None, None, None, 'CN3.12'),
    ('PA9', 'i', None, None, None, 'CN3.1'),
    ('PA10', 'i', None, None, None, 'CN3.2'),
    ('PA11', 'i', None, None, None, 'CN3.13'),
    ('PA12', 'i', None, None, None, 'CN3.5'),
    ('PA13', 'i', None, None, None, 'swdio'),
    ('PA14', 'i', None, None, None, 'swclk'),
    ('PA15', 'i', None, None, None, 'VCP_RX'),

    ('PB0', 'i', None, None, None, 'CN3.6'),
    ('PB1', 'i', None, None, None, 'CN3.9'),
    #('PB2', 'i', None, None, None, ''),
    ('PB3', 'i', None, None, None, 'CN4.15/LD3 green'),
    ('PB4', 'i', None, None, None, 'CN3.15'),
    ('PB5', 'i', None, None, None, 'CN3.14'),
    ('PB6', 'i', None, None, None, 'CN3.8'),
    ('PB7', 'i', None, None, None, 'CN3.7'),
    ('PB8', 'i', None, None, None, 'BOOT0'),
    #('PB9', 'i', None, None, None, ''),
    #('PB10', 'i', None, None, None, ''),
    #('PB11', 'i', None, None, None, ''),
    #('PB12', 'i', None, None, None, ''),
    #('PB13', 'i', None, None, None, ''),
    #('PB14', 'i', None, None, None, ''),
    #('PB15', 'i', None, None, None, ''),

    ('PF0', 'i', None, None, None, 'CN3.10'),
    ('PF1', 'i', None, None, None, 'CN3.11'),
)

# -----------------------------------------------------------------------------

class target(object):
  """nucleo-l432kc Nucleo32 Board with STM32L432KCU6 SoC"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.stm32l4x2(self.device), self.device, self.mem)
    gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    self.gpio = gpio.gpio(gpio_drv)
    #self.i2c = i2c.i2c(i2c_driver.gpio(gpio_drv, 'PB6', 'PB7'))

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
      #('i2c', self.i2c.menu, 'i2c functions'),
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
    self.ui.cli.set_prompt('\n%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------
