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

# map device.soc_name to the set of GPIOs
gpio_set = {
  #'STM32F303xC': STM32F303xC_gpio,
  'STM32F407xx': ('A','B','C','D','E','F','G','H','I'),
}

#-----------------------------------------------------------------------------

class drv(object):
  """GPIO driver for ST devices"""

  def __init__(self, device, cfg = None):
    self.device = device
    self.cfg = cfg
    self.ports = ['GPIO%s' % x for x in gpio_set[self.device.soc_name]]

  def __name(self, port, bit):
    """return the standard name for the port/pin"""
    return 'P%s%d' % (port[4:], (bit & 15))

  def name_arg(self, name):
    """convert a standard name into a port/bit tuple or None"""
    if len(name) > 4:
      return None
    name = name.upper()
    if not name.startswith('P'):
      return None
    port = 'GPIO%s' % name[1]
    if not port in self.ports:
      return None
    try:
      pin = int(name[2:])
    except:
      return None
    if pin > 15:
      return None
    return (port, pin)

  def rd_output(self, port, bit = None):
    """read the output value"""
    hw = self.device.peripherals[port]
    val = hw.ODR.rd()
    if bit is None:
      return val
    return (val >> (bit & 15)) & 1

  def rd_input(self, port, bit = None):
    """read the input value"""
    hw = self.device.peripherals[port]
    val = hw.IDR.rd()
    if bit is None:
      return val
    return (val >> (bit & 15)) & 1

  def wr(self, port, val):
    """write the output value"""
    hw = self.device.peripherals[port]
    hw.ODR.wr(val)

  def set_bit(self, port, bit):
    """set an output bit"""
    hw = self.device.peripherals[port]
    hw.BSRR.wr(1 << (bit & 15))

  def clr_bit(self, port, bit):
    """clear an output bit"""
    hw = self.device.peripherals[port]
    hw.BSRR.wr(1 << ((bit & 15) + 16))

  def status(self, port):
    """return a status string for the named gpio port"""
    s = []
    hw = self.device.peripherals[port]
    mode_val =  hw.MODER.rd()
    for i in range(16):
      # standard driver name
      std_name = self.__name(port, i)
      # target name
      tgt_name = None
      if self.cfg.has_key(std_name):
        tgt_name = self.cfg[std_name][0]
      # mode for this pin
      mode_name = hw.MODER.fields['MODER%d' % i].field_name(mode_val)
      val_name = ''
      af_name = None
      if mode_name == 'analog':
        mode_name = 'a'
      if mode_name == 'altfunc':
        mode_name = 'f'
        if i < 8:
          af_name = hw.AFRL.fields['AFRL%d' % i].field_name(hw.AFRL.rd())
        else:
          af_name = hw.AFRH.fields['AFRH%d' % i].field_name(hw.AFRH.rd())
      elif mode_name == 'output':
        mode_name = 'o'
        val_name = '%d' % self.rd_output(port, i)
      elif mode_name == 'input':
        mode_name = 'i'
        val_name = '%d' % self.rd_input(port, i)
      # combine the target and alternate function name
      if tgt_name:
        if af_name:
          tgt_name += ' (%s)' % af_name
      else:
        tgt_name = (af_name, '')[af_name is None]
      s.append([std_name, mode_name, val_name, tgt_name])
    return s

  def __str__(self):
    s = []
    for p in self.ports:
      s.extend(self.status(p))
    return util.display_cols(s)

#-----------------------------------------------------------------------------
