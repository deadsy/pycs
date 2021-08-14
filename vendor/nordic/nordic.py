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
# GPIO Registers

_gpio_dir_enumset = (
  ('Input', 0, None),
  ('Output', 1, None),
)

_gpio_pin_cnf_fieldset = (
  ('SENSE',17,16, None, 'Pin sensing mechanism'),
  ('DRIVE',10,8, None, 'Drive configuration'),
  ('PULL',3,2, None, 'Pull configuration'),
  ('INPUT',1,1, None, 'Connect/Disconnect Input Buffer'),
  ('DIR',0,0, _gpio_dir_enumset, 'Pin direction'),
)

_gpio_dir_fieldset = (
  ('PIN0', 0, 0, _gpio_dir_enumset, 'Px.0 pin'),
  ('PIN1', 1, 1, _gpio_dir_enumset, 'Px.1 pin'),
  ('PIN2', 2, 2, _gpio_dir_enumset, 'Px.2 pin'),
  ('PIN3', 3, 3, _gpio_dir_enumset, 'Px.3 pin'),
  ('PIN4', 4, 4, _gpio_dir_enumset, 'Px.4 pin'),
  ('PIN5', 5, 5, _gpio_dir_enumset, 'Px.5 pin'),
  ('PIN6', 6, 6, _gpio_dir_enumset, 'Px.6 pin'),
  ('PIN7', 7, 7, _gpio_dir_enumset, 'Px.7 pin'),
  ('PIN8', 8, 8, _gpio_dir_enumset, 'Px.8 pin'),
  ('PIN9', 9, 9, _gpio_dir_enumset, 'Px.9 pin'),
  ('PIN10', 10, 10, _gpio_dir_enumset, 'Px.10 pin'),
  ('PIN11', 11, 11, _gpio_dir_enumset, 'Px.11 pin'),
  ('PIN12', 12, 12, _gpio_dir_enumset, 'Px.12 pin'),
  ('PIN13', 13, 13, _gpio_dir_enumset, 'Px.13 pin'),
  ('PIN14', 14, 14, _gpio_dir_enumset, 'Px.14 pin'),
  ('PIN15', 15, 15, _gpio_dir_enumset, 'Px.15 pin'),
  ('PIN16', 16, 16, _gpio_dir_enumset, 'Px.16 pin'),
  ('PIN17', 17, 17, _gpio_dir_enumset, 'Px.17 pin'),
  ('PIN18', 18, 18, _gpio_dir_enumset, 'Px.18 pin'),
  ('PIN19', 19, 19, _gpio_dir_enumset, 'Px.19 pin'),
  ('PIN20', 20, 20, _gpio_dir_enumset, 'Px.20 pin'),
  ('PIN21', 21, 21, _gpio_dir_enumset, 'Px.21 pin'),
  ('PIN22', 22, 22, _gpio_dir_enumset, 'Px.22 pin'),
  ('PIN23', 23, 23, _gpio_dir_enumset, 'Px.23 pin'),
  ('PIN24', 24, 24, _gpio_dir_enumset, 'Px.24 pin'),
  ('PIN25', 25, 25, _gpio_dir_enumset, 'Px.25 pin'),
  ('PIN26', 26, 26, _gpio_dir_enumset, 'Px.26 pin'),
  ('PIN27', 27, 27, _gpio_dir_enumset, 'Px.27 pin'),
  ('PIN28', 28, 28, _gpio_dir_enumset, 'Px.28 pin'),
  ('PIN29', 29, 29, _gpio_dir_enumset, 'Px.29 pin'),
  ('PIN30', 30, 30, _gpio_dir_enumset, 'Px.30 pin'),
  ('PIN31', 31, 31, _gpio_dir_enumset, 'Px.31 pin'),
)

_gpio_regset = (
  ('OUT'        , 32, 0x504, None, 'Write GPIO port'),
  ('OUTSET'     , 32, 0x508, None, 'Set individual bits in GPIO port'),
  ('OUTCLR'     , 32, 0x50c, None, 'Clear individual bits in GPIO port'),
  ('IN'         , 32, 0x510, None, 'Read GPIO port'),
  ('DIR'        , 32, 0x514, _gpio_dir_fieldset, 'Direction of GPIO pins'),
  ('DIRSET'     , 32, 0x518, None, 'DIR set register'),
  ('DIRCLR'     , 32, 0x51c, None, 'DIR clear register'),
  ('LATCH'      , 32, 0x520, None, 'Latch for PIN_CNF[n].SENSE'),
  ('DETECTMODE' , 32, 0x524, None, 'Select between DETECT/LDETECT'),
  ('PIN_CNF0'   , 32, 0x700, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF1'   , 32, 0x704, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF2'   , 32, 0x708, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF3'   , 32, 0x70c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF4'   , 32, 0x710, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF5'   , 32, 0x714, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF6'   , 32, 0x718, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF7'   , 32, 0x71c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF8'   , 32, 0x720, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF9'   , 32, 0x724, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF10'  , 32, 0x728, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF11'  , 32, 0x72c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF12'  , 32, 0x730, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF13'  , 32, 0x734, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF14'  , 32, 0x738, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF15'  , 32, 0x73c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF16'  , 32, 0x740, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF17'  , 32, 0x744, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF18'  , 32, 0x748, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF19'  , 32, 0x74c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF20'  , 32, 0x750, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF21'  , 32, 0x754, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF22'  , 32, 0x758, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF23'  , 32, 0x75c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF24'  , 32, 0x760, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF25'  , 32, 0x764, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF26'  , 32, 0x768, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF27'  , 32, 0x76c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF28'  , 32, 0x770, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF29'  , 32, 0x774, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF30'  , 32, 0x778, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
  ('PIN_CNF31'  , 32, 0x77c, _gpio_pin_cnf_fieldset, 'Configuration of GPIO pins'),
)

#-----------------------------------------------------------------------------
# nRF51822

def nRF51822_fixup(d):
  d.soc_name = 'nRF51822'
  d.cpu_info.deviceNumInterrupts = 32
  # memory and misc peripherals
  d.insert(soc.make_peripheral('ram', 0x20000000, 16 << 10, None, 'Data RAM'))
  # This device has FICR.CLENR0 = 0xffffffff indicating that the code 0 region does not exist
  d.insert(soc.make_peripheral('flash', 0, 256 << 10, None, 'Code FLASH'))

s = soc_info()
s.name = 'nRF51822'
s.svd = 'nrf51'
s.fixups = (nRF51822_fixup, cmregs.cm0_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------
# nRF52832

def nRF52832_fixup(d):
  d.soc_name = 'nRF52832'
  d.cpu_info.nvicPrioBits = 3
  d.cpu_info.deviceNumInterrupts = 39 # Note: reference manual has 37, svd file has 39
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.FPU)
  # memory and misc peripherals
  d.insert(soc.make_peripheral('ram', 0x20000000, 64 << 10, None, 'Data RAM'))
  d.insert(soc.make_peripheral('flash', 0, 512 << 10, None, 'Code FLASH'))

s = soc_info()
s.name = 'nRF52832'
s.svd = 'nrf52'
s.fixups = (nRF52832_fixup, cmregs.cm4_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------
# nRF52833

def nRF52833_fixup(d):
  d.soc_name = 'nRF52833'
  d.cpu_info.nvicPrioBits = 3
  d.cpu_info.deviceNumInterrupts = 39 # Note: reference manual has 37, svd file has 39
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.FPU)
  # memory and misc peripherals
  d.insert(soc.make_peripheral('ram', 0x20000000, 128 << 10, None, 'Data RAM'))
  d.insert(soc.make_peripheral('flash', 0, 512 << 10, None, 'Code FLASH'))
  # 2nd gpio port
  d.insert(soc.make_peripheral('P1', 0x50000300, 4 << 10, _gpio_regset, 'GPIO Port 2'))

s = soc_info()
s.name = 'nRF52833'
s.svd = 'nrf52'
s.fixups = (nRF52833_fixup, cmregs.cm4_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not name in soc_db:
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
