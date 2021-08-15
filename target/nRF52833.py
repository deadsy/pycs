# -----------------------------------------------------------------------------
"""

Nordic nRF52833-DK Development Board (nRF52833)

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

import vendor.nordic.nordic as vendor
import vendor.nordic.flash as flash_driver
import vendor.nordic.gpio as gpio_driver
import vendor.nordic.i2c as i2c_driver

# -----------------------------------------------------------------------------

soc_name = 'nRF52833'
prompt = 'nRF52833dk'

# -----------------------------------------------------------------------------

# built in jlink
default_itf = {
  'name': 'jlink',
  'vid': 0x1366,
  'pid': 0x1015,
  'itf': 2,
}

# -----------------------------------------------------------------------------
# GPIO Pin Assignments

# pin, sense_mode, drive_mode, pull_mode, input_mode, dir_mode, name
gpio_cfg = (
  ('P0.0', None, None, None, None, None, 'D14/XL1',),
  ('P0.1', None, None, None, None, None, 'D15/XL2',),
  ('P0.2', None, None, None, None, None, 'AREF',),
  ('P0.3', None, None, None, None, None, 'A0',),
  ('P0.4', None, None, None, None, None, 'A1/CTS_OPTIONAL',),
  ('P0.5', None, None, None, None, None, 'D16/RTS',),
  ('P0.6', None, None, None, None, None, 'D17/TXD',),
  ('P0.7', None, None, None, None, None, 'D18/TRACECLK/CTS_DEFAULT',),
  ('P0.8', None, None, None, None, None, 'D19/RXD',),
  ('P0.9', None, None, None, None, None, 'D20',),
  ('P0.10', None, None, None, None, None, 'D21',),
  ('P0.11', None, None, None, None, None, 'D22/BUTTON1_DEFAULT/TRACEDATA2',),
  ('P0.12', None, None, None, None, None, 'D23/BUTTON2_DEFAULT/TRACEDATA1',),
  ('P0.13', None, None, None, None, None, 'D24/LED1',),
  ('P0.14', None, None, None, None, None, 'D25/LED2',),
  ('P0.15', None, None, None, None, None, 'D26/LED3',),
  ('P0.16', None, None, None, None, None, 'D27/LED4',),
  ('P0.17', None, None, None, None, None, 'D8',),
  ('P0.18', None, None, None, None, None, 'D28/RESET',),
  ('P0.19', None, None, None, None, None, 'D9',),
  ('P0.20', None, None, None, None, None, 'D10',),
  ('P0.21', None, None, None, None, None, 'D11',),
  ('P0.22', None, None, None, None, None, 'D12',),
  ('P0.23', None, None, None, None, None, 'D13',),
  ('P0.24', None, None, None, None, None, 'D29/BUTTON3',),
  ('P0.25', None, None, None, None, None, 'D30/BUTTON4',),
  ('P0.26', None, None, None, None, None, 'SDA',),
  ('P0.27', None, None, None, None, None, 'SCL',),
  ('P0.28', None, None, None, None, None, 'A2',),
  ('P0.29', None, None, None, None, None, 'A3',),
  ('P0.30', None, None, None, None, None, 'A4',),
  ('P0.31', None, None, None, None, None, 'A5',),

  ('P1.0', None, None, None, None, None, 'D31/SWO/TRACEDATA0',),
  ('P1.1', None, None, None, None, None, 'D0',),
  ('P1.2', None, None, None, None, None, 'D1',),
  ('P1.3', None, None, None, None, None, 'D2',),
  ('P1.4', None, None, None, None, None, 'D3',),
  ('P1.5', None, None, None, None, None, 'D4',),
  ('P1.6', None, None, None, None, None, 'D5',),
  ('P1.7', None, None, None, None, None, 'D6/BUTTON1_OPTIONAL',),
  ('P1.8', None, None, None, None, None, 'D7/BUTTON2_OPTIONAL',),
  ('P1.9', None, None, None, None, None, 'D32/TRACEDATA3',),
)

# -----------------------------------------------------------------------------

class target(object):
  """Nordic nRF52833 Developer's Kit"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio
    self.device = vendor.get_device(self.ui, soc_name)
    self.dbgio.connect(self.device.cpu_info.name, 'swd')
    self.cpu = cortexm.cortexm(self, ui, self.dbgio, self.device)
    self.device.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)
    self.flash = flash.flash(flash_driver.flash(self.device), self.device, self.mem)
    gpio_drv = (gpio_driver.drv(self.device, gpio_cfg))
    self.gpio = gpio.gpio(gpio_drv)
    self.i2c = i2c.i2c(i2c_driver.bitbang(gpio_drv, 'P0.27', 'P0.26'))
    # setup the rtt client
    ram = self.device.ram
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
