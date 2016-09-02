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
# Device Information
# Silabs doesn't put these in the SVD file :-(

_device_info_regset = (
  ('CMU_LFRCOCTRL', 32, 0x020, None, 'Register reset value'),
  ('CMU_HFRCOCTRL', 32, 0x028, None, 'Register reset value'),
  ('CMU_AUXHFRCOCTRL', 32, 0x030, None, 'Register reset value'),
  ('ADC0_CAL', 32, 0x040, None, 'Register reset value'),
  ('ADC0_BIASPROG', 32, 0x048, None, 'Register reset value'),
  ('DAC0_CAL', 32, 0x050, None, 'Register reset value'),
  ('DAC0_BIASPROG', 32, 0x058, None, 'Register reset value'),
  ('ACMP0_CTRL', 32, 0x060, None, 'Register reset value'),
  ('ACMP1_CTRL', 32, 0x068, None, 'Register reset value'),
  ('CMU_LCDCTRL', 32, 0x078, None, 'Register reset value'),
  ('DAC0_OPACTRL', 32, 0x0A0, None, 'Register reset value'),
  ('DAC0_OPAOFFSET', 32, 0x0A8, None, 'Register reset value'),
  ('DI_CRC', 16, 0x1B0, None, ''),
  ('CAL_TEMP_0', 8, 0x1B2, None, ''),
  ('ADC0_CAL_1V25', 16, 0x1B4, None, ''),
  ('ADC0_CAL_2V5', 16, 0x1B6, None, ''),
  ('ADC0_CAL_VDD', 16, 0x1B8, None, ''),
  ('ADC0_CAL_5VDIFF', 16, 0x1BA, None, ''),
  ('ADC0_CAL_2XVDD', 16, 0x1BC, None, ''),
  ('ADC0_TEMP_0_READ_1V25', 16, 0x1BE, None, ''),
  ('DAC0_CAL_1V25', 32, 0x1C8, None, ''),
  ('DAC0_CAL_2V5', 32, 0x1CC, None, ''),
  ('DAC0_CAL_VDD', 32, 0x1D0, None, ''),
  ('AUXHFRCO_CALIB_BAND_1', 8, 0x1D4, None, ''),
  ('AUXHFRCO_CALIB_BAND_7', 8, 0x1D5, None, ''),
  ('AUXHFRCO_CALIB_BAND_11', 8, 0x1D6, None, ''),
  ('AUXHFRCO_CALIB_BAND_14', 8, 0x1D7, None, ''),
  ('AUXHFRCO_CALIB_BAND_21', 8, 0x1D8, None, ''),
  ('AUXHFRCO_CALIB_BAND_28', 8, 0x1D9, None, ''),
  ('HFRCO_CALIB_BAND_1', 8, 0x1DC, None, ''),
  ('HFRCO_CALIB_BAND_7', 8, 0x1DD, None, ''),
  ('HFRCO_CALIB_BAND_11', 8, 0x1DE, None, ''),
  ('HFRCO_CALIB_BAND_14', 8, 0x1DF, None, ''),
  ('HFRCO_CALIB_BAND_21', 8, 0x1E0, None, ''),
  ('HFRCO_CALIB_BAND_28', 8, 0x1E1, None, ''),
  ('MEM_INFO_PAGE_SIZE', 8, 0x1E7, None, ''),
  ('UNIQUE_0', 32, 0x1F0, None, ''),
  ('UNIQUE_1', 32, 0x1F4, None, ''),
  ('MEM_INFO_FLASH', 16, 0x1F8, None, ''),
  ('MEM_INFO_RAM', 16, 0x1FA, None, ''),
  ('PART_NUMBER', 16, 0x1FC, None, ''),
  ('PART_FAMILY', 8, 0x1FE, None, ''),
  ('PROD_REV', 8, 0x1FF, None, ''),
)

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

def EFM32LG990F256_fixup(d):
  d.soc_name = 'EFM32LG990F256'
  d.cpu_info.nvicPrioBits = 3
  d.cpu_info.deviceNumInterrupts = 40
  # memory and misc periperhals
  d.insert(soc.make_peripheral('flash', 0x00000000, 256 << 10, None, 'flash'))
  d.insert(soc.make_peripheral('sram', 0x20000000, 32 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('DI', 0x0FE08000, 0x200, _device_info_regset, 'Device Information'))

s = soc_info()
s.name = 'EFM32LG990F256'
s.svd = 'EFM32LG990F256'
s.fixups = (EFM32LG990F256_fixup, cmregs.cm3_fixup)
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
