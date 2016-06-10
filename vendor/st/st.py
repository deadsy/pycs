#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequecies.

"""
#-----------------------------------------------------------------------------

import soc
import cmregs

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

#-----------------------------------------------------------------------------

def STM32F407xx_fixup(d):
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 80
  d.remove(d.NVIC)
  d.insert(soc.make_peripheral('sram', 0x20000000, 128 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('ccm_sram', 0x10000000, 8 << 10, None, 'core coupled memory sram'))
  d.insert(soc.make_peripheral('flash_system', 0x1fff0000, 30 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 1 << 20, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_option', 0x1fffc000, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('flash_otp', 0x1fff7800, 528, None, 'flash otp memory'))

s = soc_info()
s.name = 'STM32F407xx'
s.svd = 'STM32F40x'
s.fixups = (STM32F407xx_fixup, cmregs.cm4_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/st/svd/%s.svd.gz' % info.svd
  ui.put('%s: compiling %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device

#-----------------------------------------------------------------------------
