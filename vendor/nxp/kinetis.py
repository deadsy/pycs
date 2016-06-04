#-----------------------------------------------------------------------------
"""

SoC file for NXP Kinetis Devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequecies.

"""
#-----------------------------------------------------------------------------

import soc
import cmregs
import cortexm

#-----------------------------------------------------------------------------

def cm4_fixup(d):
  d.cpu_info.name = 'CM4'
  d.cpu_info.nvicPrioBits = 4
  # nvic
  d.deviceNumInterrupts = 106
  d.remove(d.NVIC)
  d.insert(cmregs.build_nvic(d.deviceNumInterrupts))
  # systick
  d.remove(d.SysTick)
  d.insert(cmregs.systick)
  # scb
  d.remove(d.SystemControl)
  d.insert(cmregs.cm3_scb)
  d.insert(cmregs.cm4_fpu)
  cortexm.add_system_exceptions(d)

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

s = soc_info()
s.name = 'MK64FN1M0VLL12'
s.svd = 'MK64F12'
s.fixups = (cm4_fixup,)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/nxp/svd/%s.svd.gz' % info.svd
  ui.put('%s: building %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device

#-----------------------------------------------------------------------------
