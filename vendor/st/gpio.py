#-----------------------------------------------------------------------------
"""
GPIO Driver for ST Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

"""
#-----------------------------------------------------------------------------

import util

#-----------------------------------------------------------------------------

# STM32F40x/STM32F41x
STM32F40x_gpio = (
  ('GPIOA', 'PA'),
  ('GPIOB', 'PB'),
  ('GPIOC', 'PC'),
  ('GPIOD', 'PD'),
  ('GPIOE', 'PE'),
  ('GPIOF', 'PF'),
  ('GPIOG', 'PG'),
  ('GPIOH', 'PH'),
  ('GPIOI', 'PI'),
)

# map device.soc_name to the gpio map
gpio_map = {
  #'STM32F303xC': STM32F303xC_gpio,
  'STM32F407xx': STM32F40x_gpio,
}

#-----------------------------------------------------------------------------

class drv(object):
  """GPIO driver for ST devices"""

  def __init__(self, device, cfg = None):
    self.device = device
    self.cfg = cfg
    self.ports = gpio_map[self.device.soc_name]

  def status(self, port):
    """return a status string for the named gpio port"""
    s = []
    (name, prefix) = port
    hw = self.device.peripherals[name]
    mode_val =  hw.MODER.rd()

    for i in range(16):
      # standard driver name
      std_name = '%s%d' % (prefix, i)
      # target name
      tgt_name = ''
      if self.cfg.has_key(std_name):
        tgt_name = self.cfg[std_name][0]
      mode_name = hw.MODER.fields['MODER%d' % i].field_name(mode_val)
      s.append([std_name, mode_name, tgt_name,])
    return s

  def __str__(self):
    s = []
    for p in self.ports:
      s.extend(self.status(p))
    return util.display_cols(s)

#-----------------------------------------------------------------------------
