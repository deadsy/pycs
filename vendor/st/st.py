#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequacies.

"""
#-----------------------------------------------------------------------------

import soc
import mem
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
  ('STM32L4x2', 0x435, None),
  ('STM32F05x', 0x440, None),
  ('STM32F09x', 0x442, None),
  ('STM32F03x', 0x444, None),
  ('STM32F04x', 0x445, None),
  ('STM32F07x', 0x448, None),
  ('STM32F303xD/E,STM32F398xE', 0x446, None),
)

# Most devices have this in their SVD.
# STM32L432KC doesn't...

_IDCODE_fieldset = (
  ('REV_ID', 31, 16, _rev_id_enumset, 'Revision Identifier'),
  ('DEV_ID', 11, 0, _dev_id_enumset, 'Device Identifier'),
)

_DBGMCU_regset = (
  ('IDCODE', 32, 0x00, _IDCODE_fieldset, 'MCU Device ID Code Register'),
  ('CR', 32, 0x04, None, 'Debug MCU Configuration Register'),
  ('APB1FZR1', 32, 0x08, None, 'APB1 freeze register1'),
  ('APB1FZR2', 32, 0x0C, None, 'APB1 freeze register2'),
  ('APB2FZR', 32, 0x10, None, 'APB2 freeze register'),
)

#-----------------------------------------------------------------------------
# more gpio decoding

# GPIOx.MODER
_gpio_moder_enumset = (
  ('input', 0, None),
  ('output', 1, None),
  ('altfunc', 2, None),
  ('analog', 3, None),
)

# GPIOx.OTYPER
_gpio_otyper_enumset = (
  ('push pull', 0, None),
  ('open drain', 1, None),
)

# GPIOx.OSPEEDR
_gpio_ospeedr_enumset = (
  ('low speed', 0, None),
  ('medium speed', 1, None),
  ('fast speed', 2, None),
  ('high speed', 3, None),
)

# GPIOx.PUPDR
_gpio_pupdr_enumset = (
  ('no pu/pd', 0, None),
  ('pull up', 1, None),
  ('pull down', 2, None),
)

# Alternate Function Decodes
# ST doesn't put these in the SVD file :-(

# port, pin, af, name
_STM32F407xx_altfunc = (
  # this is a partial list
  ('A', 0, 1, 'TIM2_CH1_ETR'),
  ('A', 0, 2, 'TIM5_CH1'),
  ('A', 0, 3, 'TIM8_ETR'),
  ('A', 0, 7, 'USART2_CTS'),
  ('A', 0, 8, 'UART4_TX'),
  ('A', 0, 11, 'ETH_MII_CRS'),
  ('A', 0, 15, 'EVENTOUT'),
  ('A', 2, 1, 'TIM2_CH3'),
  ('A', 2, 2, 'TIM5_CH3'),
  ('A', 2, 3, 'TIM9_CH1'),
  ('A', 2, 7, 'USART2_TX'),
  ('A', 2, 11, 'ETH_MDIO'),
  ('A', 2, 15, 'EVENTOUT'),
  ('A', 3, 1, 'TIM2_CH4'),
  ('A', 3, 2, 'TIM5_CH4'),
  ('A', 3, 3, 'TIM9_CH2'),
  ('A', 3, 7, 'USART2_RX'),
  ('A', 3, 10, 'OTG_HS_ULPI_D0'),
  ('A', 3, 11, 'ETH_MII_COL'),
  ('A', 3, 15, 'EVENTOUT'),
  ('A', 4, 5, 'SPI1_NSS'),
  ('A', 4, 6, 'SPI3_NSS/I2S3_WS'),
  ('A', 4, 7, 'USART2_CK'),
  ('A', 4, 12, 'OTG_HS_SOF'),
  ('A', 4, 13, 'DCMI_HSYNC'),
  ('A', 4, 15, 'EVENTOUT'),
  ('A', 8, 0, 'MCO1'),
  ('A', 8, 1, 'TIM1_CH1'),
  ('A', 8, 4, 'I2C3_SCL'),
  ('A', 8, 7, 'USART1_CK'),
  ('A', 8, 10, 'OTG_FS_SOF'),
  ('A', 8, 15, 'EVENTOUT'),
  ('A', 13, 0, 'JTMS-SWDIO'),
  ('A', 13, 15, 'EVENTOUT'),
  ('A', 14, 0, 'JTCK-SWCLK'),
  ('A', 14, 15, 'EVENTOUT'),
  ('A', 15, 0, 'JTDI'),
  ('A', 15, 1, 'TIM2_CH1/TIM2_ETR'),
  ('A', 15, 5, 'SPI1_NSS'),
  ('A', 15, 6, 'SPI3_NSS/I2S3_WS'),
  ('A', 15, 15, 'EVENTOUT'),
  ('B', 2, 15, 'EVENTOUT'),
  ('B', 3, 0, 'JTDO/TRACESWO'),
  ('B', 3, 1, 'TIM2_CH2'),
  ('B', 3, 5, 'SPI1_SCK'),
  ('B', 3, 6, 'SPI3_SCK/I2S3_CK'),
  ('B', 3, 15, 'EVENTOUT'),
  ('B', 4, 0, 'NJTRST'),
  ('B', 4, 2, 'TIM3_CH1'),
  ('B', 4, 5, 'SPI1_MISO'),
  ('B', 4, 6, 'SPI3_MISO'),
  ('B', 4, 7, 'I2S3ext_SD'),
  ('B', 4, 15, 'EVENTOUT'),
  ('B', 6, 2, 'TIM4_CH1'),
  ('B', 6, 4, 'I2C1_SCL'),
  ('B', 6, 7, 'USART1_TX'),
  ('B', 6, 9, 'CAN2_TX'),
  ('B', 6, 13, 'DCMI_D5'),
  ('B', 6, 15, 'EVENTOUT'),
  ('B', 7, 2, 'TIM4_CH2'),
  ('B', 7, 4, 'I2C1_SDA'),
  ('B', 7, 7, 'USART1_RX'),
  ('B', 7, 12, 'FSMC_NL'),
  ('B', 7, 13, 'DCMI_VSYNC'),
  ('B', 7, 15, 'EVENTOUT'),
  ('B', 9, 2, 'TIM4_CH4'),
  ('B', 9, 3, 'TIM11_CH1'),
  ('B', 9, 4, 'I2C1_SDA'),
  ('B', 9, 5, 'SPI2_NSS/I2S2_WS'),
  ('B', 9, 9, 'CAN1_TX'),
  ('B', 9, 12, 'SDIO_D5'),
  ('B', 9, 13, 'DCMI_D7'),
  ('B', 9, 15, 'EVENTOUT'),
  ('C', 7, 2, 'TIM3_CH2'),
  ('C', 7, 3, 'TIM8_CH2'),
  ('C', 7, 6, 'I2S3_MCK'),
  ('C', 7, 8, 'USART6_RX'),
  ('C', 7, 12, 'SDIO_D7'),
  ('C', 7, 13, 'DCMI_D1'),
  ('C', 7, 15, 'EVENTOUT'),
  ('C', 10, 6, 'SPI3_SCK/I2S3_CK'),
  ('C', 10, 7, 'USART3_TX'),
  ('C', 10, 8, 'UART4_TX'),
  ('C', 10, 12, 'SDIO_D2'),
  ('C', 10, 13, 'DCMI_D8'),
  ('C', 10, 15, 'EVENTOUT'),
  ('C', 12, 6, 'SPI3_MOSI/I2S3_SD'),
  ('C', 12, 7, 'USART3_CK'),
  ('C', 12, 8, 'UART5_TX'),
  ('C', 12, 12, 'SDIO_CK'),
  ('C', 12, 13, 'DCMI_D9'),
  ('C', 12, 15, 'EVENTOUT'),
)

# port, pin, af, name
_STM32F429xI_altfunc = (
  # this is a partial list
  ('A', 3, 14, 'LCD_B5'),
  ('A', 4, 14, 'LCD_VSYNC'),
  ('A', 5, 1, 'TIM2_CH1/TIM2_ETR'),
  ('A', 6, 14, 'LCD_G2'),
  ('A', 8, 14, 'LCD_R6'),
  ('A', 9, 7, 'USART1_TX'),
  ('A', 10, 7, 'USART1_RX'),
  ('A', 11, 14, 'LCD_R4'),
  ('A', 12, 14, 'LCD_R5'),
  ('B', 8, 14, 'LCD_B6'),
  ('B', 9, 14, 'LCD_B7'),
  ('B', 10, 14, 'LCD_G4'),
  ('B', 11, 14, 'LCD_G5'),
  ('C', 6, 14, 'LCD_HSYNC'),
  ('C', 7, 14, 'LCD_G6'),
  ('C', 10, 14, 'LCD_R2'),
  ('D', 3, 14, 'LCD_G7'),
  ('D', 6, 14, 'LCD_B2'),
  ('D', 10, 14, 'LCD_B3'),
  ('E', 4, 14, 'LCD_B0'),
  ('E', 5, 14, 'LCD_G0'),
  ('E', 6, 14, 'LCD_G1'),
  ('E', 11, 14, 'LCD_G3'),
  ('E', 12, 14, 'LCD_B4'),
  ('E', 13, 14, 'LCD_DE'),
  ('E', 14, 14, 'LCD_CLK'),
  ('E', 15, 14, 'LCD_R7'),
  ('F', 10, 14, 'LCD_DE'),
  ('G', 6, 14, 'LCD_R7'),
  ('G', 7, 14, 'LCD_CLK'),
  ('G', 10, 14, 'LCD_B2'),
  ('G', 11, 14, 'LCD_B3'),
  ('G', 12, 14, 'LCD_B1'),
)

# port, pin, af, name
_STM32L432KC_altfunc = (
  # this is a partial list
)

# port, pin, af, name
_STM32F091xC_altfunc = (
  # this is a partial list
)

# port, pin, af, name
_STM32F303xC_altfunc = (
  # this is a partial list
  ('A', 11, 6, 'TIM1_CH1N'),
  ('A', 11, 7, 'USART1_CTS'),
  ('A', 11, 8, 'COMP1_OUT'),
  ('A', 11, 9, 'CAN_RX'),
  ('A', 11, 10, 'TIM4_CH1'),
  ('A', 11, 11, 'TIM1_CH4'),
  ('A', 11, 12, 'TIM1_BKIN2'),
  ('A', 11, 14, 'USB_DM'),
  ('A', 11, 15, 'EVENTOUT'),
  ('A', 12, 1, 'TIM16_CH1'),
  ('A', 12, 6, 'TIM1_CH2N'),
  ('A', 12, 7, 'USART1_RTS_DE'),
  ('A', 12, 8, 'COMP2_OUT'),
  ('A', 12, 9, 'CAN_TX'),
  ('A', 12, 10, 'TIM4_CH2'),
  ('A', 12, 11, 'TIM1_ETR'),
  ('A', 12, 14, 'USB_DP'),
  ('A', 12, 15, 'EVENTOUT'),
  ('A', 13, 0, 'SWDIO/JTMS'),
  ('A', 13, 1, 'TIM16_CH1N'),
  ('A', 13, 3, 'TSC_G4_IO3'),
  ('A', 13, 5, 'IR_OUT'),
  ('A', 13, 7, 'USART3_CTS'),
  ('A', 13, 10, 'TIM4_CH3'),
  ('A', 13, 15, 'EVENTOUT'),
  ('A', 14, 0, 'SWCLK/JTCK'),
  ('A', 14, 3, 'TSC_G4_IO4'),
  ('A', 14, 4, 'I2C1_SDA'),
  ('A', 14, 5, 'TIM8_CH2'),
  ('A', 14, 6, 'TIM1_BKIN'),
  ('A', 14, 7, 'USART2_TX'),
  ('A', 14, 15, 'EVENTOUT'),
  ('A', 15, 0, 'JTDI'),
  ('A', 15, 1, 'TIM2_CH1_ETR'),
  ('A', 15, 2, 'TIM8_CH1'),
  ('A', 15, 4, 'I2C1_SCL'),
  ('A', 15, 5, 'SPI1_NSS'),
  ('A', 15, 6, 'SPI3_NSS/I2S3_WS'),
  ('A', 15, 7, 'USART2_RX'),
  ('A', 15, 9, 'TIM1_BKIN'),
  ('A', 15, 15, 'EVENTOUT'),
  ('B', 3, 0, 'JTDO/TRACESWO'),
  ('B', 3, 1, 'TIM2_CH2'),
  ('B', 3, 2, 'TIM4_ETR'),
  ('B', 3, 3, 'TSC_G5_IO1'),
  ('B', 3, 4, 'TIM8_CH1N'),
  ('B', 3, 5, 'SPI1_SCK'),
  ('B', 3, 6, 'SPI3_SCK/I2S3_CK'),
  ('B', 3, 7, 'USART2_TX'),
  ('B', 3, 10, 'TIM3_ETR'),
  ('B', 3, 15, 'EVENTOUT'),
  ('B', 4, 0, 'NJTRST'),
  ('B', 4, 1, 'TIM16_CH1'),
  ('B', 4, 2, 'TIM3_CH1'),
  ('B', 4, 3, 'TSC_G5_IO2'),
  ('B', 4, 4, 'TIM8_CH2N'),
  ('B', 4, 5, 'SPI1_MISO'),
  ('B', 4, 6, 'SPI3_MISO/I2S3ext_SD'),
  ('B', 4, 7, 'USART2_RX'),
  ('B', 4, 10, 'TIM17_BKIN'),
  ('B', 4, 15, 'EVENTOUT'),
)

def gpio_altfunc_enums(port, pin, altfunc):
  """return an enumeration set for the given port and pin"""
  enums = []
  for (portx, pinx, af, name) in altfunc:
    if port == portx and pin == pinx:
      enums.append((name, af, None))
  return enums

def gpio_decodes(d, ports, altfunc):
  """setup additional gpio field decodes not in the svd file"""
  for p in ports:
    gpio = d.peripherals['GPIO%s' % p]
    for i in range(16):
      f = gpio.MODER.fields['MODER%d' % i]
      f.enumvals = soc.make_enumvals(f, _gpio_moder_enumset)
      f = gpio.OTYPER.fields['OT%d' % i]
      f.enumvals = soc.make_enumvals(f, _gpio_otyper_enumset)
      f = gpio.OSPEEDR.fields['OSPEEDR%d' % i]
      f.enumvals = soc.make_enumvals(f, _gpio_ospeedr_enumset)
      f = gpio.PUPDR.fields['PUPDR%d' % i]
      f.enumvals = soc.make_enumvals(f, _gpio_pupdr_enumset)
      if i < 8:
        f = gpio.AFRL.fields['AFRL%d' % i]
      else:
        f = gpio.AFRH.fields['AFRH%d' % i]
      f.enumvals = soc.make_enumvals(f, gpio_altfunc_enums(p, i, altfunc))

#-----------------------------------------------------------------------------

def STM32F407xx_fixup(d):
  d.soc_name = 'STM32F407xx'
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 80
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.NVIC)
  # more decode for the DBG registers
  f = d.DBG.DBGMCU_IDCODE.REV_ID
  f.enumvals = soc.make_enumvals(f, _rev_id_enumset)
  f = d.DBG.DBGMCU_IDCODE.DEV_ID
  f.enumvals = soc.make_enumvals(f, _dev_id_enumset)
  # more decode for the GPIO registers
  gpio_decodes(d, ('A','B','C','D','E','F','G','H','I'), _STM32F407xx_altfunc)
  # memory and misc periperhals
  d.insert(soc.make_peripheral('sram', 0x20000000, 128 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('ccm_sram', 0x10000000, 8 << 10, None, 'core coupled memory sram'))
  d.insert(soc.make_peripheral('flash_system', 0x1fff0000, 30 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 1 << 20, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_option', 0x1fffc000, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('flash_otp', 0x1fff7800, 528, None, 'flash otp memory'))
  d.insert(soc.make_peripheral('UID', 0x1fff7a10, 12, _uuid_regset, 'Unique Device ID'))
  d.insert(soc.make_peripheral('FLASH_SIZE', 0x1fff7a22, 2, _flash_size_regset, 'Flash Size'))
  # the size of these peripherals seems wrong
  d.OTG_HS_GLOBAL.size = 1 << 10
  d.OTG_HS_PWRCLK.size = 1 << 10
  # ram buffer for flash writing
  d.rambuf = mem.region('rambuf', 0x20000000 + 512, 32 << 10)

s = soc_info()
s.name = 'STM32F407xx'
s.svd = 'STM32F40x'
s.fixups = (STM32F407xx_fixup, cmregs.cm4_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def STM32F429xI_fixup(d):
  d.soc_name = 'STM32F429xI'
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 90
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.NVIC)
  # more decode for the DBG registers
  f = d.DBG.DBGMCU_IDCODE.REV_ID
  f.enumvals = soc.make_enumvals(f, _rev_id_enumset)
  f = d.DBG.DBGMCU_IDCODE.DEV_ID
  f.enumvals = soc.make_enumvals(f, _dev_id_enumset)
  # fix up the OSPEEDR labels ST messed up
  for x in ('A','B','C','D','E','F','G','H','I','J','K'):
    d.peripherals['GPIO%c' % x].rename_register('GPIOB_OSPEEDR', 'OSPEEDR')
  # more decode for the GPIO registers
  gpio_decodes(d, ('A','B','C','D','E','F','G','H','I','J','K'), _STM32F429xI_altfunc)
  # memory and misc periperhals
  d.insert(soc.make_peripheral('sram', 0x20000000, 256 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('ccm_sram', 0x10000000, 64 << 10, None, 'core coupled memory sram'))
  d.insert(soc.make_peripheral('flash_system', 0x1fff0000, 30 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 2 << 20, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_opt_bank1', 0x1fffc000, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('flash_opt_bank2', 0x1ffec000, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('flash_otp', 0x1fff7800, 528, None, 'flash otp memory'))
  d.insert(soc.make_peripheral('UID', 0x1fff7a10, 12, _uuid_regset, 'Unique Device ID'))
  d.insert(soc.make_peripheral('FLASH_SIZE', 0x1fff7a22, 2, _flash_size_regset, 'Flash Size'))
  # the size of this peripheral seems wrong
  d.OTG_HS_PWRCLK.size = 1 << 10
  # ram buffer for flash writing
  d.rambuf = mem.region('rambuf', 0x20000000 + 512, 32 << 10)

s = soc_info()
s.name = 'STM32F429xI'
s.svd = 'STM32F429x'
s.fixups = (STM32F429xI_fixup, cmregs.cm4_fixup)
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
  # more decode for the GPIO registers
  gpio_decodes(d, ('A','B','C','D','E','F'), _STM32F303xC_altfunc)
  # memory and misc periperhals
  d.insert(soc.make_peripheral('sram', 0x20000000, 40 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('ccm_sram', 0x10000000, 8 << 10, None, 'core coupled memory sram'))
  d.insert(soc.make_peripheral('flash_system', 0x1fffd800, 8 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 256 << 10, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_option', 0x1ffff800, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('UID', 0x1ffff7ac, 12, _uuid_regset, 'Unique Device ID'))
  d.insert(soc.make_peripheral('FLASH_SIZE', 0x1ffff7cc, 2, _flash_size_regset, 'Flash Size'))
  # ram buffer for flash writing
  d.rambuf = mem.region('rambuf', 0x20000000 + 512, 32 << 10)

s = soc_info()
s.name = 'STM32F303xC'
s.svd = 'STM32F30x'
s.fixups = (STM32F303xC_fixup, cmregs.cm4_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def STM32L432KC_fixup(d):
  d.soc_name = 'STM32L432KC'
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 84
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.NVIC)
  # ST didn't put DBGMCU in the SVD, so we will add it.
  d.insert(soc.make_peripheral('DBGMCU', 0xe0042000, 1 << 10, _DBGMCU_regset, 'Debug support'))
  # more decode for the GPIO registers
  gpio_decodes(d, ('A','B','C','D','E','H'), _STM32L432KC_altfunc)
  # memory and misc periperhals
  d.insert(soc.make_peripheral('sram1', 0x20000000, 48 << 10, None, 'sram1'))
  # sram2 is found in 2 regions of the memory map
  d.insert(soc.make_peripheral('sram2a', 0x2000c000, 16 << 10, None, 'sram2'))
  d.insert(soc.make_peripheral('sram2b', 0x10000000, 16 << 10, None, 'sram2'))
  d.insert(soc.make_peripheral('flash_system', 0x1fff0000, 28 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 256 << 10, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_otp', 0x1fff7000, 1 << 10, None, 'flash otp memory'))
  d.insert(soc.make_peripheral('flash_option', 0x1fff7800, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('UID', 0x1fff7590, 12, _uuid_regset, 'Unique Device ID'))
  d.insert(soc.make_peripheral('FLASH_SIZE', 0x1fff75e0, 2, _flash_size_regset, 'Flash Size'))
  # ram buffer for flash writing
  d.rambuf = mem.region('rambuf', 0x20000000 + 512, 32 << 10)

s = soc_info()
s.name = 'STM32L432KC'
s.svd = 'STM32L4x2'
s.fixups = (STM32L432KC_fixup, cmregs.cm4_fixup)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def STM32F091xC_fixup(d):
  d.soc_name = 'STM32F091xC'
  d.cpu_info.deviceNumInterrupts = 32
  # remove some core peripherals - we'll replace them in the cpu fixup
  d.remove(d.NVIC)
  # More decode for the DBGMCU registers
  f = d.DBGMCU.IDCODE.REV_ID
  f.enumvals = soc.make_enumvals(f, _rev_id_enumset)
  f = d.DBGMCU.IDCODE.DEV_ID
  f.enumvals = soc.make_enumvals(f, _dev_id_enumset)
  # more decode for the GPIO registers
  gpio_decodes(d, ('A','B','C','D','E','F'), _STM32F091xC_altfunc)
  # memory and misc periperhals
  d.insert(soc.make_peripheral('sram', 0x20000000, 32 << 10, None, 'sram'))
  d.insert(soc.make_peripheral('flash_system', 0x1fffd800, 8 << 10, None, 'flash system memory'))
  d.insert(soc.make_peripheral('flash_main', 0x08000000, 256 << 10, None, 'flash main memory'))
  d.insert(soc.make_peripheral('flash_option', 0x1ffff800, 16, None, 'flash option memory'))
  d.insert(soc.make_peripheral('UID', 0x1ffff7ac, 12, _uuid_regset, 'Unique Device ID'))
  d.insert(soc.make_peripheral('FLASH_SIZE', 0x1ffff7cc, 2, _flash_size_regset, 'Flash Size'))
  # ram buffer for flash writing
  d.rambuf = mem.region('rambuf', 0x20000000 + 512, 24 << 10)

s = soc_info()
s.name = 'STM32F091xC'
s.svd = 'STM32F0x1'
s.fixups = (STM32F091xC_fixup, cmregs.cm0_fixup)
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
