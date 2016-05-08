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

class soc(object):
  """Atmel SAM SoC"""

  def __init__(self, cpu, device):
    self.cpu = cpu
    self.menu = (
      ('exceptions', 'show exception status', self.cmd_exceptions),
    )
    if device == 'ATSAML21J18B':
      self.exceptions = cortexm.build_exceptions(soc_vector_table0)
      self.priority_bits = 4
    else:
      assert False, 'unknown SoC device %s' % device

  def cmd_exceptions(self, ui, args):
    """display the exceptions table"""
    ui.put('%s\n' % cortexm.exceptions_str(self.cpu, self))

#-----------------------------------------------------------------------------
