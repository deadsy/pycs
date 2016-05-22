#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

"""
#-----------------------------------------------------------------------------

import cortexm
from regs import fld, fld_set, reg32, reg16, reg8, regset, memio


#-----------------------------------------------------------------------------
# System Configuration

def MEM_MODE_format(x):
  modes = {
    0: 'flash_main@0',
    1: 'flash_system@0',
    2: 'fsmc_bank1@0',
    3: 'sram@0',
  }
  return '(%d) %s' % (x, modes.get(x, '?'))

f = []
f.append(fld('MEM_MODE', 1, 0, MEM_MODE_format))
MEMRMP_fields = fld_set('MEMRMP', f)

# STM32F405xx/07xx and STM32F415xx/17xx
r = []
r.append(reg32('MEMRMP', 0x00, MEMRMP_fields))
r.append(reg32('PMC', 0x04))
r.append(reg32('EXTICR1', 0x08))
r.append(reg32('EXTICR2', 0x0c))
r.append(reg32('EXTICR3', 0x10))
r.append(reg32('EXTICR4', 0x14))
r.append(reg32('CMPCR', 0x20))
syscfg_regs0 = regset('system configuration controller', r)

#-----------------------------------------------------------------------------
# Flash

# STM32F303xB/C/D/E, STM32F303x6/8, STM32F328x8, STM32F358xC, STM32F398xE
r = []
r.append(reg32('ACR', 0x00))
r.append(reg32('KEYR', 0x04))
r.append(reg32('OPTKEYR', 0x08))
r.append(reg32('SR', 0x0C))
r.append(reg32('CR', 0x10))
r.append(reg32('AR',0x14))
r.append(reg32('OBR', 0x1C))
r.append(reg32('WRPR', 0x20))
flash_regs0 = regset('flash interface', r)

# STM32F405xx/07xx and STM32F415xx/17xx
r = []
r.append(reg32('ACR', 0x00))
r.append(reg32('KEYR', 0x04))
r.append(reg32('OPTKEYR', 0x08))
r.append(reg32('SR', 0x0C))
r.append(reg32('CR', 0x10))
r.append(reg32('OPTCR',0x14))
flash_regs1 = regset('flash interface', r)

# STM32F42xxx and STM32F43xxx
r = []
r.append(reg32('ACR', 0x00))
r.append(reg32('KEYR', 0x04))
r.append(reg32('OPTKEYR', 0x08))
r.append(reg32('SR', 0x0C))
r.append(reg32('CR', 0x10))
r.append(reg32('OPTCR',0x14))
r.append(reg32('OPTCR1',0x18))
flash_regs2 = regset('flash interface', r)

#-----------------------------------------------------------------------------
# GPIO

r = []
r.append(reg32('MODER', 0x00))
r.append(reg32('OTYPER', 0x04))
r.append(reg32('OSPEEDR', 0x08))
r.append(reg32('PUPDR', 0x0C))
r.append(reg32('IDR', 0x10))
r.append(reg32('ODR', 0x14))
r.append(reg32('BSRR', 0x18))
r.append(reg32('LCKR', 0x1C))
r.append(reg32('AFRL', 0x20))
r.append(reg32('AFRH', 0x24))
r.append(reg32('BRR', 0x28))
gpio_regs = regset('gpio', r)

#-----------------------------------------------------------------------------
# Debug MCU

def REV_ID_format(x):
  revs = {
    0x1000: 'A',
    0x1001: 'Z',
    0x1003: 'Y',
    0x1007: '1',
  }
  return '(0x%04x) Rev %s' % (x, revs.get(x, '?'))

def DEV_ID_format(x):
  devs = {
    0x413: 'STM32F405xx/07xx, STM32F415xx/17xx',
    0x419: 'STM32F42xxx, STM32F43xxx',
    0x422: 'STM32F303xB/C, STM32F358',
    0x438: 'STM32F303x6/8, STM32F328',
    0x446: 'STM32F303xD/E, STM32F398xE',
  }
  return '(0x%03x) %s' % (x, devs.get(x, '?'))

f = []
f.append(fld('REV_ID', 31, 16, REV_ID_format))
f.append(fld('DEV_ID', 11, 0, DEV_ID_format))
IDCODE_fields = fld_set('IDCODE', f)

r = []
r.append(reg32('IDCODE', 0x00, IDCODE_fields))
r.append(reg32('CR', 0x04))
r.append(reg32('APB1_FZ', 0x08))
r.append(reg32('APB2_FZ', 0x08))
dbgmcu_regs = regset('debug mcu', r)

#-----------------------------------------------------------------------------
# STM32F3 devices

# Vector Tables
# irq_number : name

# STM32F303xB/C/D/E, STM32F358xC and STM32F398xE
stm32f3_vtable0 = {
  0: 'WWDG',
  1: 'PVD',
  2: 'TAMPER_STAMP',
  3: 'RTC_WKUP',
  4: 'FLASH',
  5: 'RCC',
  6: 'EXTI0',
  7: 'EXTI1',
  8: 'EXTI2_TS',
  9: 'EXTI3',
  10: 'EXTI4',
  11: 'DMA1_Channel1',
  12: 'DMA1_Channel2',
  13: 'DMA1_Channel3',
  14: 'DMA1_Channel4',
  15: 'DMA1_Channel5',
  16: 'DMA1_Channel6',
  17: 'DMA1_Channel7',
  18: 'ADC1_2',
  19: 'USB_HP/CAN_TX',
  20: 'USB_LP/CAN_RX0',
  21: 'CAN_RX1',
  22: 'CAN_SCE',
  23: 'EXTI9_5',
  24: 'TIM1_BRK/TIM15',
  25: 'TIM1_UP/TIM16',
  26: 'TIM1_TRG_COM/TIM17',
  27: 'TIM1_CC',
  28: 'TIM2',
  29: 'TIM3',
  30: 'TIM4',
  31: 'I2C1_EV',
  32: 'I2C1_ER',
  33: 'I2C2_EV',
  34: 'I2C2_ER',
  35: 'SPI1',
  36: 'SPI2',
  37: 'USART1',
  38: 'USART2',
  39: 'USART3',
  40: 'EXTI15_10',
  41: 'RTC_Alarm',
  42: 'USBWakeUp',
  43: 'TIM8_BRK',
  44: 'TIM8_UP',
  45: 'TIM8_TRG_COM',
  46: 'TIM8_CC',
  47: 'ADC3',
  48: 'FMC',
  51: 'SPI3',
  52: 'UART4',
  53: 'UART5',
  54: 'TIM6_DAC',
  55: 'TIM7',
  56: 'DMA2_Channel1',
  57: 'DMA2_Channel2',
  58: 'DMA2_Channel3',
  59: 'DMA2_Channel4',
  60: 'DMA2_Channel5',
  61: 'ADC4',
  64: 'COMP1_2_3',
  65: 'COMP4_5_6',
  66: 'COMP7',
  72: 'I2C3_EV',
  73: 'I2C3_ER',
  74: 'USB_HP',
  75: 'USB_LP',
  76: 'USB_WakeUp_RMP',
  77: 'TIM20_BRK',
  78: 'TIM20_UP',
  79: 'TIM20_TRG_COM',
  80: 'TIM20_CC',
  81: 'FPU',
  84: 'SPI4',
}

# STM32F303x6/8and STM32F328x8
stm32f3_vtable1 = {
  0: 'WWDG',
  1: 'PVD',
  2: 'TAMPER_STAMP',
  3: 'RTC_WKUP',
  4: 'FLASH',
  5: 'RCC',
  6: 'EXTI0',
  7: 'EXTI1',
  8: 'EXTI2_TS',
  9: 'EXTI3',
  10: 'EXTI4',
  11: 'DMA1_Channel1',
  12: 'DMA1_Channel2',
  13: 'DMA1_Channel3',
  14: 'DMA1_Channel4',
  15: 'DMA1_Channel5',
  16: 'DMA1_Channel6',
  17: 'DMA1_Channel7',
  18: 'ADC1_2',
  19: 'CAN_TX',
  20: 'CAN_RX0',
  21: 'CAN_RX1',
  22: 'CAN_SCE',
  23: 'EXTI9_5',
  24: 'TIM1_BRK/TIM15',
  25: 'TIM1_UP/TIM16',
  26: 'TIM1_TRG_COM/TIM17',
  27: 'TIM1_CC',
  28: 'TIM2',
  29: 'TIM3',
  31: 'I2C1_EV',
  32: 'I2C1_ER',
  35: 'SPI1',
  37: 'USART1',
  38: 'USART2',
  39: 'USART3',
  40: 'EXTI15_10',
  41: 'RTC_Alarm',
  54: 'TIM6_DAC1',
  55: 'TIM7_DAC2',
  64: 'COMP2',
  65: 'COMP4_6',
  81: 'FPU',
}

# Memory Maps
# name: (address, size, register set)

# STM32F303xB/C and STM32F358xC
stm32f3_memmap0 = {
  'gpioa': (0x48000000, 1 << 10, gpio_regs),
  'gpiob': (0x48000400, 1 << 10, gpio_regs),
  'gpioc': (0x48000800, 1 << 10, gpio_regs),
  'gpiod': (0x48000c00, 1 << 10, gpio_regs),
  'gpioe': (0x48001000, 1 << 10, gpio_regs),
  'gpiof': (0x48001400, 1 << 10, gpio_regs),

  'adc1' : (0x50000000, 0x100, 'adc'),
  'adc2' : (0x50000100, 0x200, 'adc'),
  'adc12' : (0x50000300, 0x100, 'adc common'),
  'adc3' : (0x50000400, 0x100, 'adc'),
  'adc4' : (0x50000500, 0x200, 'adc'),
  'adc34' : (0x50000700, 0x100, 'adc common'),

  'flash': (0x40022000, 1 << 10, flash_regs0),
  'flash_option': (0x1ffff800, 2 << 10, 'flash option memory'),
  'flash_main': (0x08000000, 256 << 10, 'flash main memory'),
  'flash_system': (0x1fffd800, 8 << 10, 'flash system memory'),

  'sram': (0x20000000, 40 << 10, 'sram'),
  'ccm_sram': (0x10000000, 8 << 10, 'core coupled memory sram'),

  'tim1': (0x40012C00, 1 << 10, 'advanced control timer'),
  'tim2': (0x40000000, 1 << 10, 'general purpose timer'),
  'tim3': (0x40000400, 1 << 10, 'general purpose timer'),
  'tim4': (0x40000800, 1 << 10, 'general purpose timer'),
  'tim6': (0x40001000, 1 << 10, 'basic timer'),
  'tim7': (0x40001400, 1 << 10, 'basic timer'),
  'tim8': (0x40013400, 1 << 10, 'advanced control timer'),
  'tim15': (0x40014000, 1 << 10, 'general purpose timer'),
  'tim16': (0x40014400, 1 << 10, 'general purpose timer'),
  'tim17': (0x40014800, 1 << 10, 'general purpose timer'),

  'uart4': (0x40004c00, 1 << 10, 'uart'),
  'uart5': (0x40005000, 1 << 10, 'uart'),

  'usart1': (0x40013800, 1 << 10, 'usart'),
  'usart2': (0x40004400, 1 << 10, 'usart'),
  'usart3': (0x40004800, 1 << 10, 'usart'),

  'dbgmcu': (0xe0042000, None, dbgmcu_regs),

  #usb_sram
  #usb_fs

  #TSC
  #CRC
  #RCC
  #DMA2
  #DMA1

  #SPI1
  #EXTI
  #SYSCFG
  #COMP
  #OPAMP
  #DAC1
  #PWR
  #bxCAN
  #I2C2
  #I2C1
  #I2S3ext
  #SPI3/I2S3
  #SPI2/I2S2
  #I2S2ext
  #IWDG
  #WWDG
  #RTC

}

STM32F303xB_info = {
  'name': 'STM32F303xB',
  'memmap': stm32f3_memmap0,
}
STM32F303xC_info = {
  'name': 'STM32F303xC',
  'cpu_type': 'cortex-m4',
  'priority_bits': 4,
  'vtable': stm32f3_vtable0,
  'memmap': stm32f3_memmap0,
}
STM32F358xC_info = {
  'name': 'STM32F358xC',
  'memmap': stm32f3_memmap0,
}
STM32F303xD_info = {
  'name': 'STM32F303xD',
}
STM32F303xE_info = {
  'name': 'STM32F303xE',
}
STM32F398xE_info = {
  'name': 'STM32F398xE',
}
STM32F303x6_info = {
  'name': 'STM32F303x6',
}
STM32F303x8_info = {
  'name': 'STM32F303x8',
}
STM32F328x8_info = {
  'name': 'STM32F328x8',
}

#-----------------------------------------------------------------------------
# STM32F4 Devices

# STM32F405xx/07xxand STM32F415xx/17xx
stm32f4_vtable0 = {
  0: 'WWDG',
  1: 'PVD',
  2: 'TAMP_STAMP',
  3: 'RTC_WKUP',
  4: 'FLASH',
  5: 'RCC',
  6: 'EXTI0',
  7: 'EXTI1',
  8: 'EXTI2',
  9: 'EXTI3',
  10: 'EXTI4',
  11: 'DMA1_Stream0',
  12: 'DMA1_Stream1',
  13: 'DMA1_Stream2',
  14: 'DMA1_Stream3',
  15: 'DMA1_Stream4',
  16: 'DMA1_Stream5',
  17: 'DMA1_Stream6',
  18: 'ADC',
  19: 'CAN1_TX',
  20: 'CAN1_RX0',
  21: 'CAN1_RX1',
  22: 'CAN1_SCE',
  23: 'EXTI9_5',
  24: 'TIM1_BRK_TIM9',
  25: 'TIM1_UP_TIM10',
  26: 'TIM1_TRG_COM_TIM11',
  27: 'TIM1_CC',
  28: 'TIM2',
  29: 'TIM3',
  30: 'TIM4',
  31: 'I2C1_EV',
  32: 'I2C1_ER',
  33: 'I2C2_EV',
  34: 'I2C2_ER',
  35: 'SPI1',
  36: 'SPI2',
  37: 'USART1',
  38: 'USART2',
  39: 'USART3',
  40: 'EXTI15_10',
  41: 'RTC_Alarm',
  42: 'OTG_FS_WKUP',
  43: 'TIM8_BRK_TIM12',
  44: 'TIM8_UP_TIM13',
  45: 'TIM8_TRG_COM_TIM14',
  46: 'TIM8_CC',
  47: 'DMA1_Stream7',
  48: 'FSMC',
  49: 'SDIO',
  50: 'TIM5',
  51: 'SPI3',
  52: 'UART4',
  53: 'UART5',
  54: 'TIM6_DAC',
  55: 'TIM7',
  56: 'DMA2_Stream0',
  57: 'DMA2_Stream1',
  58: 'DMA2_Stream2',
  59: 'DMA2_Stream3',
  60: 'DMA2_Stream4',
  61: 'ETH',
  62: 'ETH_WKUP',
  63: 'CAN2_TX',
  64: 'CAN2_RX0',
  65: 'CAN2_RX1',
  66: 'CAN2_SCE',
  67: 'OTG_FS',
  68: 'DMA2_Stream5',
  69: 'DMA2_Stream6',
  70: 'DMA2_Stream7',
  71: 'USART6',
  72: 'I2C3_EV',
  73: 'I2C3_ER',
  74: 'OTG_HS_EP1_OUT',
  75: 'OTG_HS_EP1_IN',
  76: 'OTG_HS_WKUP',
  77: 'OTG_HS',
  78: 'DCMI',
  79: 'CRYP',
  80: 'HASH_RNG',
  81: 'FPU',
}

stm32f4_memmap0 = {

  'sram': (0x20000000, 128 << 10, 'sram'),
  #'ccm_sram': (0x10000000, 8 << 10, 'core coupled memory sram'),

  'flash': (0x40023c00, 1 << 10, flash_regs1),
  'flash_system': (0x1fff0000, 30 << 10, 'flash system memory'),
  'flash_main': (0x08000000, 1 << 20, 'flash main memory'),
  'flash_option': (0x1fffc000, 16, 'flash option memory'),
  'flash_otp': (0x1fff7800, 528, 'flash otp memory'),

  'gpioa': (0x40020000, 1 << 10, gpio_regs),
  'gpiob': (0x40020400, 1 << 10, gpio_regs),
  'gpioc': (0x40020800, 1 << 10, gpio_regs),
  'gpiod': (0x40020c00, 1 << 10, gpio_regs),
  'gpioe': (0x40021000, 1 << 10, gpio_regs),
  'gpiof': (0x40021400, 1 << 10, gpio_regs),
  'gpiog': (0x40021800, 1 << 10, gpio_regs),
  'gpioh': (0x40021c00, 1 << 10, gpio_regs),
  'gpioi': (0x40022000, 1 << 10, gpio_regs),
  'gpioj': (0x40022400, 1 << 10, gpio_regs),
  'gpiok': (0x40022800, 1 << 10, gpio_regs),

  'tim1': (0x40010000, 1 << 10, 'advanced control timer'),
  'tim2': (0x40000000, 1 << 10, 'general purpose timer'),
  'tim3': (0x40000400, 1 << 10, 'general purpose timer'),
  'tim4': (0x40000800, 1 << 10, 'general purpose timer'),
  'tim5': (0x40000c00, 1 << 10, 'general purpose timer'),
  'tim6': (0x40001000, 1 << 10, 'basic timer'),
  'tim7': (0x40001400, 1 << 10, 'basic timer'),
  'tim8': (0x40010400, 1 << 10, 'advanced control timer'),
  'tim9': (0x40014000, 1 << 10, 'general purpose timer'),
  'tim10': (0x40014400, 1 << 10, 'general purpose timer'),
  'tim11': (0x40014800, 1 << 10, 'general purpose timer'),
  'tim12': (0x40001800, 1 << 10, 'general purpose timer'),
  'tim13': (0x40001c00, 1 << 10, 'general purpose timer'),
  'tim14': (0x40002000, 1 << 10, 'general purpose timer'),

  'usb_otg_fs': (0x50000000, 16 << 10, 'usb on-the-go full speed'),
  'usb_otg_hs': (0x40044000, 16 << 10, 'usb on-the-go high speed'),

  'usart1': (0x40011000, 1 << 10, 'usart'),
  'usart2': (0x40004400, 1 << 10, 'usart'),
  'usart3': (0x40004800, 1 << 10, 'usart'),
  'uart4':  (0x40004c00, 1 << 10, 'uart'),
  'uart5':  (0x40005000, 1 << 10, 'uart'),
  'usart6': (0x40011400, 1 << 10, 'usart'),
  'uart7': (0x40007800, 1 << 10, 'uart'),
  'uart8': (0x40007c00, 1 << 10, 'uart'),

  'dbgmcu': (0xe0042000, None, dbgmcu_regs),

  'syscfg': (0x40013800, 1 << 10, syscfg_regs0),

  #fsmc
  #fmc
  #RNG
  #HASH
  #CRYP
  #DCMI
  #DMA2D
  #ETHERNET MAC
  #DMA2
  #DMA1
  #BKPSRAM
  #RCC
  #CRC
  #LCD-TFT
  #SAI1
  #SPI6
  #SPI5
  #EXTI
  #SPI4
  #SPI1
  #SDIO
  #ADC1 - ADC2 - ADC3
  #DAC
  #PWR
  #CAN2
  #CAN1
  #I2C3
  #I2C2
  #I2C1
  #I2S3ext
  #SPI3 / I2S3
  #SPI2 / I2S2
  #I2S2ext
  #IWDG
  #WWDG
  #RTC & BKP Registers
}

STM32F407xx_info = {
  'name': 'STM32F407xx',
  'cpu_type': 'cortex-m4',
  'priority_bits': 4,
  'vtable': stm32f4_vtable0,
  'memmap': stm32f4_memmap0,
}

#-----------------------------------------------------------------------------

soc_db = {}

def db_insert(info):
  soc_db[info['name']] = info

def lookup(name):
  if soc_db.has_key(name):
    return soc_db[name]
  assert False, 'unknown SoC device %s' % device

db_insert(STM32F303xB_info)
db_insert(STM32F303xC_info)
db_insert(STM32F358xC_info)
db_insert(STM32F303xD_info)
db_insert(STM32F303xE_info)
db_insert(STM32F398xE_info)
db_insert(STM32F303x6_info)
db_insert(STM32F303x8_info)
db_insert(STM32F328x8_info)
db_insert(STM32F407xx_info)

#-----------------------------------------------------------------------------

class soc(object):
  """stm32 SoC"""

  def __init__(self, cpu, info):
    self.cpu = cpu
    self.info = info
    self.exceptions = cortexm.build_exceptions(info['vtable'])
    self.memmap = self.build_memmap()

    self.menu = (
      ('exceptions', self.cmd_exceptions),
    )

  def build_memmap(self):
    """build the soc memory map"""
    # TODO - build the tweaked map
    return self.info['memmap']

  def cmd_exceptions(self, ui, args):
    """display exceptions table"""
    ui.put('%s\n' % cortexm.exceptions_str(self.cpu, self))

#-----------------------------------------------------------------------------
