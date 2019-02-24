#-----------------------------------------------------------------------------
"""

SoC file for Atmel SAM Devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequecies.

"""
#-----------------------------------------------------------------------------

import soc
import cmregs
import util

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

#-----------------------------------------------------------------------------
# NVM User Row Mapping: Not in the SVD :-(

def _eeprom_fmt(x):
  return '%s' % util.memsize((1 << (14-x),0)[x == 7])

def _bootprot_fmt(x):
  return '%s' % util.memsize((1 << (15-x),0)[x == 7])

_nvmr0_fieldset = (
  ('WDT_Period', 31, 28, None, 'WDT Period at power-on'),
  ('WDT_Always', 27, 27, None, 'WDT Always-On at power-on'),
  ('WDT_Enable', 26, 26, None, 'WDT Enable at power-on'),
  ('BOD12_Action', 25, 24, None, 'BOD12 Action at power-on'),
  ('BOD12_Disable', 23, 23, None, 'BOD12 Disable at power-on'),
  ('BOD12_Level', 22, 17, None, 'BOD12 threshold level at power-on'),
  ('BOD33_Action', 16, 15, None, 'BOD33 Action at power-on'),
  ('BOD33_Disable', 14, 14, None, 'BOD33 Disable at power-on'),
  ('BOD33_Level', 13, 8, None, 'BOD33 threshold level at power-on'),
  ('EEPROM', 6, 4, _eeprom_fmt, 'Used to select one of eight different EEPROM sizes'),
  ('BOOTPROT', 2, 0, _bootprot_fmt, 'Used to select one of eight different bootloader sizes'),
)

_nvmr1_fieldset = (
  ('LOCK', 31, 16, None, 'NVM Region Lock Bits'),
  ('BOD12_Hysteresis', 10, 10, None, 'BOD12 Hysteresis configuration Hysteresis at power-on'),
  ('BOD33_Hysteresis', 9, 9, None, 'BOD33 Hysteresis configuration Hysteresis at power-on'),
  ('WDT_WEN', 8, 8, None, 'WDT Timer Window Mode Enable at power-on'),
  ('WDT_EWOFFSET', 7, 4, None, 'WDT Early Warning Interrupt Time Offset at power-on'),
  ('WDT_Window', 3, 0, None, 'WDT Window mode time-out at power-on'),
)

_nvm_user_row_regset = (
  ('NVMUR0', 32, 0x0, _nvmr0_fieldset, 'NVM User Row 0'),
  ('NVMUR1', 32, 0x4, _nvmr1_fieldset, 'NVM User Row 1'),
)

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
  d.insert(soc.make_peripheral('NVMUR', 0x00804000, 8, _nvm_user_row_regset, 'NVM User Row'))

s = soc_info()
s.name = 'ATSAML21J18B'
s.svd = 'ATSAML21J18B'
s.fixups = (ATSAML21J18B_fixup, cmregs.cm0plus_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not name in soc_db:
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
