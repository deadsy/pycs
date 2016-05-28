#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

"""
#-----------------------------------------------------------------------------

import importlib
import cortexm

#-----------------------------------------------------------------------------

def svd_info(name):
  """return the svd device information"""
  module = importlib.import_module('soc.st.%s' % name)
  return module.device

#-----------------------------------------------------------------------------

soc_db = {}

def db_insert(info):
  soc_db[info['name']] = info

def lookup(name):
  if soc_db.has_key(name):
    info = soc_db[name]
    # read in the device from the svd file
    svd = svd_info(info['svd'])
    info['cpu'] = svd['cpu']
    info['memmap'] = svd['memmap']
    info['vtable'] = svd['vtable']
    return info
  assert False, 'unknown SoC device %s' % device

#-----------------------------------------------------------------------------

STM32F303xB_info = {
  'name': 'STM32F303xB',
}
db_insert(STM32F303xB_info)

STM32F303xC_info = {
  'name': 'STM32F303xC',
}
db_insert(STM32F303xC_info)

STM32F358xC_info = {
  'name': 'STM32F358xC',
}
db_insert(STM32F358xC_info)

STM32F303xD_info = {
  'name': 'STM32F303xD',
}
db_insert(STM32F303xD_info)

STM32F303xE_info = {
  'name': 'STM32F303xE',
}
db_insert(STM32F303xE_info)

STM32F398xE_info = {
  'name': 'STM32F398xE',
}
db_insert(STM32F398xE_info)

STM32F303x6_info = {
  'name': 'STM32F303x6',
}
db_insert(STM32F303x6_info)

STM32F303x8_info = {
  'name': 'STM32F303x8',
}
db_insert(STM32F303x8_info)

STM32F328x8_info = {
  'name': 'STM32F328x8',
}
db_insert(STM32F328x8_info)

STM32F407xx_info = {
  'name': 'STM32F407xx',
  'svd': 'STM32F40x',
}
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
