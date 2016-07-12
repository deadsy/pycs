#-----------------------------------------------------------------------------
"""

SoC file for Silicon Labs devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequacies.

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

def EFM32LG890F128_fixup(d):
  d.soc_name = 'EFM32LG890F128'
  d.cpu_info.nvicPrioBits = 3
  d.cpu_info.deviceNumInterrupts = 40

s = soc_info()
s.name = 'EFM32LG890F128'
s.svd = 'EFM32LG890F128'
s.fixups = (EFM32LG890F128_fixup, cmregs.cm3_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/silabs/svd/%s.svd.gz' % info.svd
  ui.put('%s: compiling %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device

#-----------------------------------------------------------------------------
