#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

"""
#-----------------------------------------------------------------------------

import cortexm

#-----------------------------------------------------------------------------
# SoC Exception Tables
# irq_number : name

# Table 81. STM32F303xB/C/D/E, STM32F358xC and STM32F398xE vector table
soc_vector_table0 = {
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

# Table 82. STM32F303x6/8and STM32F328x8 vector table
soc_vector_table1 = {
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

#-----------------------------------------------------------------------------

STM32F303xC_info = {
  'name': 'STM32F303xC',
  'cpu_type': 'cortex-m4',
  'priority_bits': 4,
  'vector_table': soc_vector_table0
}

#-----------------------------------------------------------------------------

soc_db = {}

def db_insert(info):
  soc_db[info['name']] = info

def lookup(name):
  if soc_db.has_key(name):
    return soc_db[name]
  assert False, 'unknown SoC device %s' % device

db_insert(STM32F303xC_info)

#-----------------------------------------------------------------------------

class soc(object):
  """stm32 SoC"""

  def __init__(self, cpu, info):
    self.cpu = cpu
    self.info = info
    self.menu = (
      ('exceptions', 'show exception status', self.cmd_exceptions),
    )
    self.exceptions = cortexm.build_exceptions(info['vector_table'])

  def cmd_exceptions(self, ui, args):
    """display the exceptions table"""
    ui.put('%s\n' % cortexm.exceptions_str(self.cpu, self))

#-----------------------------------------------------------------------------
