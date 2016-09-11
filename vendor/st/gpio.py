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

# map device.soc_name to GPIO information
# ports, rcc_enable, rcc_enable_bit_offset
gpio_info = {
  'STM32F303xC': (('A','B','C','D','E','F'), 'AHBENR', 17),
  'STM32L432KC': (('A','B','C','D','E','H'), 'AHB2ENR', 0),
  'STM32F407xx': (('A','B','C','D','E','F','G','H','I'), 'AHB1ENR', 0),
  'STM32F429xI': (('A','B','C','D','E','F','G','H','I','J','K'), 'AHB1ENR', 0),
  'STM32F091xC': (('A','B','C','D','E','F'), 'AHBENR', 17),
}

#-----------------------------------------------------------------------------

class drv(object):
  """GPIO driver for ST devices"""

  def __init__(self, device, cfg = None):
    self.device = device
    self.cfg = cfg
    self.ports = ['GPIO%s' % x for x in gpio_info[self.device.soc_name][0]]
    self.hw_init = False
    # work out the pin to name mapping from the configuration
    self.pin2name = {}
    for (pin, mode, pupd, otype, ospeed, name) in self.cfg:
      self.pin2name[pin] = name

  def __status(self, port):
    """return a status string for the named gpio port"""
    s = []
    hw = self.device.peripherals[port]
    mode_val =  hw.MODER.rd()
    for i in range(16):
      # standard pin name
      pin_name = 'P%s%d' % (port[4:], i)
      # target name
      tgt_name = self.pin2name.get(pin_name, None)
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
      s.append([pin_name, mode_name, val_name, tgt_name])
    return s

  # The following functions are the common API

  def cmd_init(self, ui, args):
    """initialise gpio hardware"""
    if self.hw_init:
      return
    # enable each gpio port in the configuration set
    ports = {}
    for (pin, mode, pupd, otype, ospeed, name) in self.cfg:
      x = self.pin_arg(pin)
      assert x is not None, 'bad gpio pin name'
      (port, bit) = x
      ports[port] = True
    [self.enable(p) for p in ports]
    # setup each pin in the configuration set
    for (pin, mode, pupd, otype, ospeed, name) in self.cfg:
      (port, bit) = self.pin_arg(pin)
      # set the pin mode
      if mode == 'i':
        # input
        self.set_mode(port, bit, 'i')
      elif mode == '0':
        # output set to 0
        self.set_mode(port, bit, 'o')
        self.clr_bit(port, bit)
      elif mode == '1':
        # output set to 1
        self.set_mode(port, bit, 'o')
        self.set_bit(port, bit)
      elif mode == 'an':
        # analog
        self.set_mode(port, bit, 'a')
      elif mode.startswith('af'):
        # alternate function AFx
        self.set_mode(port, bit, 'f')
        af = int(mode[2:])
        assert af < 16, 'bad alternate function number'
        self.set_altfunc(port, bit, af)
      else:
        assert False, 'bad gpio pin mode'
      # set the pull-up/pull-down
      self.set_pupd(port, bit, pupd)
      # set the output type
      self.set_otype(port, bit, otype)
      # set the output speed
      self.set_ospeed(port, bit, ospeed)
    self.hw_init = True
    ui.put('gpio init: ok\n')

  def pin_arg(self, name):
    """convert a standard pin name into a port/bit tuple or None"""
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

  def __str__(self):
    s = []
    for p in self.ports:
      s.extend(self.__status(p))
    return util.display_cols(s)

  # The following functions are ST specific
  # They can be called from target code - but not from generic drivers.

  def enable(self, port):
    """enable the gpio port"""
    assert port in self.ports, 'bad port name'
    port = ord(port[4:]) - ord('A')
    (_, reg, ofs) = gpio_info[self.device.soc_name]
    hw = self.device.RCC.registers[reg]
    port += ofs
    val = hw.rd()
    val &= ~(1 << port)
    val |= 1 << port
    hw.wr(val)

  def set_mode(self, port, bit, x):
    """set the pin mode"""
    hw = self.device.peripherals[port].MODER
    mode = {'i':0,'o':1,'f':2,'a':3}.get(x, 0)
    shift = (bit & 15) << 1
    val = hw.rd()
    val &= ~(3 << shift)
    val |= mode << shift
    hw.wr(val)

  def set_pupd(self, port, bit, x):
    """set the pull-up/pull-down mode"""
    hw = self.device.peripherals[port].PUPDR
    mode = {'pu':1,'pd':2}.get(x, 0)
    shift = (bit & 15) << 1
    val = hw.rd()
    val &= ~(3 << shift)
    val |= mode << shift
    hw.wr(val)

  def set_otype(self, port, bit, x):
    """set the output type"""
    hw = self.device.peripherals[port].OTYPER
    mode = {'pp':0,'od':1}.get(x, 0)
    bit &= 15
    val = hw.rd()
    val &= ~(1 << bit)
    val |= mode << bit
    hw.wr(val)

  def set_ospeed(self, port, bit, x):
    """set the output speed"""
    hw = self.device.peripherals[port].OSPEEDR
    mode = {'l':0,'m':1,'f':2,'h':3}.get(x, 0)
    shift = (bit & 15) << 1
    val = hw.rd()
    val &= ~(3 << shift)
    val |= mode << shift
    hw.wr(val)

  def set_altfunc(self, port, bit, af):
    """set the alternate function number"""
    bit &= 15
    if bit < 8:
      hw = self.device.peripherals[port].AFRL
    else:
      hw = self.device.peripherals[port].AFRH
      bit -= 8
    shift = bit << 2
    val = hw.rd()
    val &= ~(15 << shift)
    val |= af << shift
    hw.wr(val)

#-----------------------------------------------------------------------------
