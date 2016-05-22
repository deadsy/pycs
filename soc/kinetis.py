#-----------------------------------------------------------------------------
"""

SoC file for NXP Kinetis Devices

"""
#-----------------------------------------------------------------------------

import cortexm
from regs import fld, fld_set, reg32, reg16, reg8, regset, memio

#-----------------------------------------------------------------------------

# Vector Tables
# irq_number : name

vtable0 = {
}

memmap0 = {
}

MK64FN1M0VLL12_info = {
  'name': 'MK64FN1M0VLL12',
  'cpu_type': 'cortex-m4',
  'priority_bits': 4,
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

db_insert(MK64FN1M0VLL12_info)

#-----------------------------------------------------------------------------

class soc(object):
  """NXP Kinetis SoC"""

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
