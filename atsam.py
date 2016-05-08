#-----------------------------------------------------------------------------
"""

SoC file for Atmel SAM Devices

"""
#-----------------------------------------------------------------------------

import cortexm

#-----------------------------------------------------------------------------
# SoC Exception Tables
# irq_number : name

soc_vector_table0 = {

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
}

#-----------------------------------------------------------------------------

ATSAML21J18B_info = {
  'name': 'ATSAML21J18B',
  'cpu_type': 'cortex-m0+',
  'priority_bits': 2,
  'vector_table': soc_vector_table0,
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
    self.menu = (
      ('exceptions', 'show exception status', self.cmd_exceptions),
    )
    self.exceptions = cortexm.build_exceptions(info['vector_table'])

  def cmd_exceptions(self, ui, args):
    """display the exceptions table"""
    ui.put('%s\n' % cortexm.exceptions_str(self.cpu, self))

#-----------------------------------------------------------------------------
