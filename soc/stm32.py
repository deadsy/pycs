#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

"""
#-----------------------------------------------------------------------------

import importlib
import cortexm

#-----------------------------------------------------------------------------

def svd_device(name):
  module = importlib.import_module('soc.st.%s' % name)
  return module.device

#-----------------------------------------------------------------------------

STM32F303xB_info = {
  'name': 'STM32F303xB',
}
STM32F303xC_info = {
  'name': 'STM32F303xC',
}
STM32F358xC_info = {
  'name': 'STM32F358xC',
}
STM32F303xD_info = {
  'name': 'STM32F303xD',
}
STM32F303xE_info = {
  'name': 'STM32F303xE',
}
STM32F398xE_info = {
  'name': 'STM32F398xE',
}
STM32F303x6_info = {
  'name': 'STM32F303x6',
}
STM32F303x8_info = {
  'name': 'STM32F303x8',
}
STM32F328x8_info = {
  'name': 'STM32F328x8',
}
STM32F407xx_info = {
  'name': 'STM32F407xx',
  'svd': 'STM32F40x',
}

#-----------------------------------------------------------------------------

soc_db = {}

def db_insert(info):
  soc_db[info['name']] = info

def lookup(name):
  if soc_db.has_key(name):
    info = soc_db[name]
    # read in the device from the svd file
    device = svd_device(info['svd'])
    info['cpu'] = device['cpu']
    info['memmap'] = device['memmap']
    info['vtable'] = device['vtable']
    return info
  assert False, 'unknown SoC device %s' % device

db_insert(STM32F303xB_info)
db_insert(STM32F303xC_info)
db_insert(STM32F358xC_info)
db_insert(STM32F303xD_info)
db_insert(STM32F303xE_info)
db_insert(STM32F398xE_info)
db_insert(STM32F303x6_info)
db_insert(STM32F303x8_info)
db_insert(STM32F328x8_info)
db_insert(STM32F407xx_info)

#-----------------------------------------------------------------------------

class soc(object):
  """stm32 SoC"""

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
    """display exceptions table"""
    ui.put('%s\n' % cortexm.exceptions_str(self.cpu, self))

#-----------------------------------------------------------------------------
