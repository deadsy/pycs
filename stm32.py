#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

"""
#-----------------------------------------------------------------------------

import cortexm
from regs import fld, fld_set, reg32, reg16, reg8, regset, memio

#-----------------------------------------------------------------------------
# Flash

r = []
r.append(reg32('ACR', 0x00))
r.append(reg32('KEYR', 0x04))
r.append(reg32('OPTKEYR', 0x08))
r.append(reg32('SR', 0x0C))
r.append(reg32('CR', 0x10))
r.append(reg32('AR',0x14))
r.append(reg32('OBR', 0x1C))
r.append(reg32('WRPR', 0x20))
flash_regs = regset('flash interface', r)

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
# STM32F3 devices

# Vector Tables
# irq_number : name

# STM32F303xB/C/D/E, STM32F358xC and STM32F398xE
vtable0 = {
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
vtable1 = {
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
memmap0 = {
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

  'flash': (0x40022000, 1 << 10, flash_regs),
  'flash_option': (0x1ffff800, 2 << 10, 'flash option memory'),
  'flash_main': (0x08000000, 256 << 10, 'flash main memory'),
  'flash_system': (0x1fffd800, 8 << 10, 'flash system memory'),

  'sram': (0x20000000, 40 << 10, 'sram'),
  'ccm_sram': (0x10000000, 8 << 10, 'ccm_sram'),

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
  'memmap': memmap0,
}
STM32F303xC_info = {
  'name': 'STM32F303xC',
  'cpu_type': 'cortex-m4',
  'priority_bits': 4,
  'vtable': vtable0,
  'memmap': memmap0,
}
STM32F358xC_info = {
  'name': 'STM32F358xC',
  'memmap': memmap0,
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
