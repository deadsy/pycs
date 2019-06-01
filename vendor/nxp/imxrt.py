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

#-----------------------------------------------------------------------------

def MIMXRT1021_fixup(d):
  d.soc_name = 'MIMXRT1021'
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 176
  # memory
  d.insert(soc.make_peripheral('itcm', 0x00000000, 256 << 10, None, 'ITCM'))
  d.insert(soc.make_peripheral('romcp', 0x00200000, 96 << 10, None, 'Boot ROM'))
  d.insert(soc.make_peripheral('dtcm', 0x20000000, 256 << 10, None, 'DTCM'))
  d.insert(soc.make_peripheral('ocram', 0x20200000, 256 << 10, None, 'On Chip RAM'))
  d.insert(soc.make_peripheral('flexspi_memory', 0x60000000, 504 << 20, None, 'FlexSPI Memory'))
  d.insert(soc.make_peripheral('flexspi_rxfifo', 0x7fc00000, 4 << 20, None, 'FlexSPI Rx FIFO'))
  d.insert(soc.make_peripheral('flexspi_txfifo', 0x7f800000, 4 << 20, None, 'FlexSPI Tx FIFO'))
  d.insert(soc.make_peripheral('semc_memory', 0x80000000, 1536 << 20, None, 'SEMC Memory'))

s = soc_info()
s.name = 'MIMXRT1021DAG5A'
s.svd = 'MIMXRT1021'
s.fixups = (MIMXRT1021_fixup, cmregs.cm7_fixup,)
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
