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
# ST typically doesn't provide cpu information in the SVD files
# These functions are used to provide the required data.

def cm4_fixup(d):
  d.cpu_info.name = 'CM4'
  d.cpu_info.nvicPrioBits = 4
  d.insert(cmregs.systick)
  d.insert(cmregs.cm3_scb)
  d.insert(cmregs.cm3_mpu)
  d.insert(cmregs.cm4_fpu)

#-----------------------------------------------------------------------------

def STM32F407xx_fixup(d):
  # some of the peripherals have weird sizes.
  # set them to None so the memory map looks nicer
  d.OTG_HS_GLOBAL.size = None
  d.OTG_HS_PWRCLK.size = None
  d.NVIC.size = None

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

s = soc_info()
s.name = 'STM32F407xx'
s.svd = 'STM32F40x'
s.fixups = (cm4_fixup, STM32F407xx_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/st/svd/%s.svd.gz' % info.svd
  ui.put('%s: building %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device

#-----------------------------------------------------------------------------
