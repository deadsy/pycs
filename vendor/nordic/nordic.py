#-----------------------------------------------------------------------------
"""

SoC file for Nordic devices

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
# nRF51822

def nRF51822_fixup(d):
  d.cpu_info.deviceNumInterrupts = 32
  d.insert(soc.make_peripheral('ram', 0x20000000, 16 << 10, None, 'Data RAM'))
  # This device has FICR.CLENR0 = 0xffffffff indicating that the code 0 region does not exit
  d.insert(soc.make_peripheral('flash1', 0, 256 << 10, None, 'FLASH Code Region 1'))

s = soc_info()
s.name = 'nRF51822'
s.svd = 'nrf51'
s.fixups = (nRF51822_fixup, cmregs.cm0_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/nordic/svd/%s.svd.gz' % info.svd
  ui.put('%s: compiling %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device

#-----------------------------------------------------------------------------
