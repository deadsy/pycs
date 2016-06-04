#-----------------------------------------------------------------------------
"""

SoC file for Atmel SAM Devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequecies.

"""
#-----------------------------------------------------------------------------

import soc
import cmregs
import cortexm

def cm0plus_fixup(d):
  d.cpu_info.name = 'CM0+'
  d.cpu_info.nvicPrioBits = 2
  d.deviceNumInterrupts = 32
  d.insert(cmregs.build_nvic(d.deviceNumInterrupts))
  d.insert(cmregs.systick)
  d.insert(cmregs.cm0_scb)
  cortexm.add_system_exceptions(d)

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

s = soc_info()
s.name = 'ATSAML21J18B'
s.svd = 'ATSAML21J18B'
s.fixups = (cm0plus_fixup,)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/atmel/svd/%s.svd.gz' % info.svd
  ui.put('%s: building %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device

#-----------------------------------------------------------------------------
