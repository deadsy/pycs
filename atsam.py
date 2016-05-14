#-----------------------------------------------------------------------------
"""

SoC file for Atmel SAM Devices

"""
#-----------------------------------------------------------------------------

import cortexm
from regs import fld, fld_set, reg32, reg16, reg8, regset, memio

#-----------------------------------------------------------------------------
# Watch Dog Timer

r = []
r.append(reg8('CTRLA', 0x00))
r.append(reg8('CONFIG', 0x01))
r.append(reg8('EWCTRL', 0x02))
r.append(reg8('INTENCLR', 0x04))
r.append(reg8('INTENSET', 0x05))
r.append(reg8('INTFLAG', 0x06))
r.append(reg32('SYNCBUSY', 0x08))
r.append(reg8('CLEAR', 0x0c))
wdt_regs = regset('watch dog timer', r)

#-----------------------------------------------------------------------------
# Non-Volatile Memory Controller

r = []
r.append(reg16('CTRLA', 0x00))
r.append(reg32('CTRLB', 0x04))
r.append(reg32('PARAM', 0x08))
r.append(reg8('INTENCLR', 0x0c))
r.append(reg8('INTENSET', 0x10))
r.append(reg8('INTFLAG', 0x14))
r.append(reg16('STATUS', 0x18))
r.append(reg32('ADDR', 0x1c))
r.append(reg16('LOCK', 0x20))
nvmctrl_regs = regset('non-volatile memory controller', r)

#-----------------------------------------------------------------------------
# IO Pin Controller

r = []
r.append(reg32('DIR', 0x00))
r.append(reg32('DIRCLR', 0x04))
r.append(reg32('DIRSET', 0x08))
r.append(reg32('DIRTGL', 0x0c))
r.append(reg32('OUT', 0x10))
r.append(reg32('OUTCLR', 0x14))
r.append(reg32('OUTSET', 0x18))
r.append(reg32('OUTTGL', 0x1c))
r.append(reg32('IN', 0x20))
r.append(reg32('CTRL', 0x24))
r.append(reg32('WRCONFIG', 0x28))
r.append(reg32('EVCTRL', 0x2c))
r.append(reg8('PMUXn0', 0x30))
r.append(reg8('PMUXn1', 0x31))
r.append(reg8('PMUXn2', 0x32))
r.append(reg8('PMUXn3', 0x33))
r.append(reg8('PMUXn4', 0x34))
r.append(reg8('PMUXn5', 0x35))
r.append(reg8('PMUXn6', 0x36))
r.append(reg8('PMUXn7', 0x37))
r.append(reg8('PMUXn8', 0x38))
r.append(reg8('PMUXn9', 0x39))
r.append(reg8('PMUXn10', 0x3a))
r.append(reg8('PMUXn11', 0x3b))
r.append(reg8('PMUXn12', 0x3c))
r.append(reg8('PMUXn13', 0x3d))
r.append(reg8('PMUXn14', 0x3e))
r.append(reg8('PMUXn15', 0x3f))
r.append(reg8('PINCFG0', 0x40))
r.append(reg8('PINCFG1', 0x41))
r.append(reg8('PINCFG2', 0x42))
r.append(reg8('PINCFG3', 0x43))
r.append(reg8('PINCFG4', 0x44))
r.append(reg8('PINCFG5', 0x45))
r.append(reg8('PINCFG6', 0x46))
r.append(reg8('PINCFG7', 0x47))
r.append(reg8('PINCFG8', 0x48))
r.append(reg8('PINCFG9', 0x49))
r.append(reg8('PINCFG10', 0x4a))
r.append(reg8('PINCFG11', 0x4b))
r.append(reg8('PINCFG12', 0x4c))
r.append(reg8('PINCFG13', 0x4d))
r.append(reg8('PINCFG14', 0x4e))
r.append(reg8('PINCFG15', 0x4f))
r.append(reg8('PINCFG16', 0x50))
r.append(reg8('PINCFG17', 0x51))
r.append(reg8('PINCFG18', 0x52))
r.append(reg8('PINCFG19', 0x53))
r.append(reg8('PINCFG20', 0x54))
r.append(reg8('PINCFG21', 0x55))
r.append(reg8('PINCFG22', 0x56))
r.append(reg8('PINCFG23', 0x57))
r.append(reg8('PINCFG24', 0x58))
r.append(reg8('PINCFG25', 0x59))
r.append(reg8('PINCFG26', 0x5a))
r.append(reg8('PINCFG27', 0x5b))
r.append(reg8('PINCFG28', 0x5c))
r.append(reg8('PINCFG29', 0x5d))
r.append(reg8('PINCFG30', 0x5e))
r.append(reg8('PINCFG31', 0x5f))
port_regs = regset('port i/o pin controller', r)

#-----------------------------------------------------------------------------

# Vector Tables
# irq_number : name

vtable0 = {

  0: 'Various',
  # PM - Power Manager
  # MCLK Main Clock
  # OSCCTRL - Oscillators Controller
  # OSC32KCTRL - 32KHz Oscillators Controller
  # SUPC - Supply Controller
  # PAC - Protecion Access Controller

  1: 'WDT', # Watchdog Timer
  2: 'RTC', # Real Time Counter
  3: 'EIC', # External Interrupt Controller
  4: 'NVMCTRL', #  Non-Volatile Memory Controller
  5: 'DMAC', # Direct Memory Access Controller
  6: 'USB', # Universal Serial Bus
  7: 'EVSYS', # Event System
  8: 'SERCOM0', # Serial Communication Interface 0
  9: 'SERCOM1', # Serial Communication Interface 1
  10: 'SERCOM2', # Serial Communication Interface 2
  11: 'SERCOM3', # Serial Communication Interface 3
  12: 'SERCOM4', # Serial Communication Interface 4
  13: 'SERCOM5', # Serial Communication Interface 5
  14: 'TCC0', # Timer Counter for Control 0
  15: 'TCC1', # Timer Counter for Control 1
  16: 'TCC2', # Timer Counter for Control 2
  17: 'TC0', # Timer Counter 0
  18: 'TC1', # Timer Counter 1
  19: 'TC2', # Timer Counter 2
  20: 'TC3', # Timer Counter 3
  21: 'TC4', # Timer Counter 4
  22: 'ADC', # Analog-to-Digital Converter
  23: 'AC', # Analog Comparator
  24: 'DAC', # Digital-to-Analog Converter
  25: 'PTC', # Peripheral Touch Controller
  26: 'AES', # Advanced Encrytpion Standard module
  27: 'TRNG', # True Random Number Generator
  28: 'IRQ28', # ?
}

memmap0 = {
  'flash': (0, 256 << 10, 'flash'),
  'rww_flash': (0x00400000, 8 << 10, 'read while write flash'),
  'sram': (0x20000000, 32 << 10, 'sram'),
  'lp_sram': (0x30000000, 8 << 10, 'low power sram'),

  'wdt': (0x40001c00, 1 << 10, wdt_regs),
  'nvmctrl': (0x41004000,1 << 10,nvmctrl_regs),
  'port': (0x40002800,1 << 10,port_regs),
}

#TODO we need a more comprehensive set of options passed through to the cpu defn.

ATSAML21J18B_info = {
  'name': 'ATSAML21J18B',
  'cpu_type': 'cortex-m0+',
  'priority_bits': 2,
  'vtable': vtable0,
  'memmap': memmap0,
}

#-----------------------------------------------------------------------------

soc_db = {}

def db_insert(info):
  soc_db[info['name']] = info

def lookup(name):
  if soc_db.has_key(name):
    return soc_db[name]
  assert False, 'unknown SoC device %s' % device

db_insert(ATSAML21J18B_info)

#-----------------------------------------------------------------------------

class soc(object):
  """Atmel SAM SoC"""

  def __init__(self, cpu, info):
    self.cpu = cpu
    self.info = info
    self.exceptions = cortexm.build_exceptions(info['vtable'])
    self.memmap = self.build_memmap()

    self.menu = (
      ('exceptions', self.cmd_exceptions),
    )

  def build_memmap(self):
    """build the soc memory map"""
    # TODO - build the tweaked map
    return self.info['memmap']

  def cmd_exceptions(self, ui, args):
    """display the exceptions table"""
    ui.put('%s\n' % cortexm.exceptions_str(self.cpu, self))

#-----------------------------------------------------------------------------
