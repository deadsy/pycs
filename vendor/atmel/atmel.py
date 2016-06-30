#-----------------------------------------------------------------------------
"""

SoC file for Atmel SAM Devices

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
# ATSAML21J18B

def ATSAML21J18B_fixup(d):
  d.soc_name = 'ATSAML21J18B'
  d.cpu_info.deviceNumInterrupts = 32
  # memory and misc periperhals
  d.insert(soc.make_peripheral('flash', 0x00000000, 256 << 10, None, 'Flash'))
  d.insert(soc.make_peripheral('rww',  0x00400000, 8 << 10, None, 'RWW Section'))
  d.insert(soc.make_peripheral('sram', 0x20000000, 32 << 10, None, 'SRAM'))
  d.insert(soc.make_peripheral('lp_sram', 0x30000000, 8 << 10, None, 'Low Power SRAM'))

s = soc_info()
s.name = 'ATSAML21J18B'
s.svd = 'ATSAML21J18B'
s.fixups = (ATSAML21J18B_fixup, cmregs.cm0plus_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/atmel/svd/%s.svd.gz' % info.svd
  ui.put('%s: compiling %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device

#-----------------------------------------------------------------------------
