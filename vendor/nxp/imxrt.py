#-----------------------------------------------------------------------------
"""

SoC file for NXP i.MX RT devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequecies.

"""
#-----------------------------------------------------------------------------

import soc
import cmregs
import cortexm

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

s = soc_info()
s.name = 'MIMXRT1021DAG5A'
s.svd = 'MIMXRT1021'
s.fixups = ( cmregs.cm7_fixup,)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not name in soc_db:
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  #svd_file = './vendor/nxp/svd/%s.svd.gz' % info.svd
  svd_file = './vendor/nxp/svd/%s.svd' % info.svd
  ui.put('%s: building %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device


#-----------------------------------------------------------------------------
