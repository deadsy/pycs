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
# Device Electronic Signature
# ST doesn't put these in the SVD file :-(

_uuid_regset = (
  ('UID0', 32, 0x00, None, 'Unique Device ID 0'),
  ('UID1', 32, 0x04, None, 'Unique Device ID 1'),
  ('UID2', 32, 0x08, None, 'Unique Device ID 2'),
)

_flash_size_regset = (
  ('FLASH_SIZE', 16, 0x0, None, 'Flash Size (in KiB)'),
)

#-----------------------------------------------------------------------------
# more enumeration decodes

# DBGMCU.IDCODE.REV_ID
_rev_id_enumset = (
  ('A', 0x1000, None),
  ('Z', 0x1001, None),
  ('Y', 0x1003, None),
  ('1', 0x1007, None),
)

# DBGMCU.IDCODE.DEV_ID
_dev_id_enumset = (
  ('STM32F405xx/07xx,STM32F415xx/17xx', 0x413, None),
  ('STM32F42xxx,STM32F43xxx', 0x419, None),
  ('STM32F303xB/C,STM32F358', 0x422, None),
  ('STM32F303x6/8,STM32F328', 0x438, None),
  ('STM32F303xD/E,STM32F398xE', 0x446, None),
)

#-----------------------------------------------------------------------------

def STM32F407xx_fixup(d):
  d.soc_name = 'STM32F407xx'
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 80
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.NVIC)
  # More decode for the DBG registers
  f = d.DBG.DBGMCU_IDCODE.REV_ID
  f.enumvals = soc.make_enumvals(f, _rev_id_enumset)
  f = d.DBG.DBGMCU_IDCODE.DEV_ID
  f.enumvals = soc.make_enumvals(f, _dev_id_enumset)
  # memory and misc periperhals
  d.insert(soc.make_peripheral('sram', 0x20000000, 128 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('ccm_sram', 0x10000000, 8 << 10, None, 'core coupled memory sram'))
  d.insert(soc.make_peripheral('flash_system', 0x1fff0000, 30 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 1 << 20, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_option', 0x1fffc000, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('flash_otp', 0x1fff7800, 528, None, 'flash otp memory'))
  d.insert(soc.make_peripheral('UID', 0x1fff7a10, 12, _uuid_regset, 'Unique Device ID'))
  d.insert(soc.make_peripheral('FLASH_SIZE', 0x1fff7a22, 2, _flash_size_regset, 'Flash Size'))

s = soc_info()
s.name = 'STM32F407xx'
s.svd = 'STM32F40x'
s.fixups = (STM32F407xx_fixup, cmregs.cm4_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def STM32F303xC_fixup(d):
  d.soc_name = 'STM32F303xC'
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 84
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.NVIC)
  d.remove(d.FPU)
  # More decode for the DBGMCU registers
  f = d.DBGMCU.IDCODE.REV_ID
  f.enumvals = soc.make_enumvals(f, _rev_id_enumset)
  f = d.DBGMCU.IDCODE.DEV_ID
  f.enumvals = soc.make_enumvals(f, _dev_id_enumset)
  # memory and misc periperhals
  d.insert(soc.make_peripheral('sram', 0x20000000, 40 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('ccm_sram', 0x10000000, 8 << 10, None, 'core coupled memory sram'))
  d.insert(soc.make_peripheral('flash_system', 0x1fffd800, 8 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 256 << 10, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_option', 0x1ffff800, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('UID', 0x1ffff7ac, 12, _uuid_regset, 'Unique Device ID'))
  d.insert(soc.make_peripheral('FLASH_SIZE', 0x1ffff7cc, 2, _flash_size_regset, 'Flash Size'))

s = soc_info()
s.name = 'STM32F303xC'
s.svd = 'STM32F30x'
s.fixups = (STM32F303xC_fixup, cmregs.cm4_fixup)
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
