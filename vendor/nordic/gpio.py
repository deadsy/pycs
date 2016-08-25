#-----------------------------------------------------------------------------
"""
GPIO Driver for Nordic Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

"""
#-----------------------------------------------------------------------------

import util

#-----------------------------------------------------------------------------

class drv(object):
  """GPIO driver for Nordic devices"""

  def __init__(self, device, cfg = None):
    self.device = device
    self.cfg = cfg
    self.ports = ['P0',]
    self.hw_init = False
    # work out the pin to name mapping from the configuration
    self.pin2name = {}
    for (pin, sense, drive, pupd, in_enable, dirn, name) in self.cfg:
      self.pin2name[pin] = name

  def __status(self, port):
    """return a status string for the named gpio port"""
    s = []
    hw = self.device.peripherals[port]
    for i in range(32):
      # standard pin name
      pin_name = '%s.%d' % (port, i)
      # target name
      tgt_name = self.pin2name.get(pin_name, None)
      # configuration for this pin
      conf = hw.registers['PIN_CNF%d' % i]
      mode_name = conf.DIR.field_name(conf.rd())
      if mode_name == 'Input':
        mode_name = 'i'
        val_name = '%d' % self.rd_input(port, i)
      elif mode_name == 'Output':
        mode_name = 'o'
        val_name = '%d' % self.rd_output(port, i)
      s.append([pin_name, mode_name, val_name, tgt_name])
    return s

  # The following functions are the common API

  def cmd_init(self, ui, args):
    """initialise gpio hardware"""
    if self.hw_init:
      return

    for (pin, sense, drive, pupd, in_enable, dirn, name) in self.cfg:
      (port, bit) = self.pin_arg(pin)
      # pin direction
      if dirn == 'o':
        self.set_dirn_out(port, bit)
      else:
        self.set_dirn_in(port, bit)
      # pin input connect/disconnect
      if in_enable:
        self.set_input_enable(port, bit)
      else:
        self.set_input_disable(port, bit)


    self.hw_init = True
    ui.put('gpio init: ok\n')

  def pin_arg(self, name):
    """convert a standard pin name into a port/bit tuple or None"""
    if len(name) > 5:
      return None
    name = name.upper()
    if not name.startswith('P'):
      return None
    port = name[:2]
    if not port in self.ports:
      return None
    try:
      pin = int(name[3:])
    except:
      return None
    if pin > 31:
      return None
    return (port, pin)

  def rd_output(self, port, bit = None):
    """read the output value"""
    hw = self.device.peripherals[port]
    val = hw.OUT.rd()
    if bit is None:
      return val
    return (val >> (bit & 31)) & 1

  def rd_input(self, port, bit = None):
    """read the input value"""
    hw = self.device.peripherals[port]
    val = hw.IN.rd()
    if bit is None:
      return val
    return (val >> (bit & 31)) & 1

  def wr(self, port, val):
    """write the output value"""
    hw = self.device.peripherals[port]
    hw.OUT.wr(val)

  def set_bit(self, port, bit):
    """set an output bit"""
    hw = self.device.peripherals[port]
    hw.OUTSET.wr(1 << (bit & 31))

  def clr_bit(self, port, bit):
    """clear an output bit"""
    hw = self.device.peripherals[port]
    hw.OUTCLR.wr(1 << (bit & 31))

  def __str__(self):
    s = []
    for p in self.ports:
      s.extend(self.__status(p))
    return util.display_cols(s)

  # The following functions are Nordic specific
  # They can be called from target code - but not from generic drivers.

  def set_dirn_out(self, port, bit):
    """set the pin direction to output"""
    hw = self.device.peripherals[port].DIRSET
    hw.wr(1 << bit)

  def set_dirn_in(self, port, bit):
    """set the pin direction to input"""
    hw = self.device.peripherals[port].DIRCLR
    hw.wr(1 << bit)

  def set_input_enable(self, port, bit):
    """enable input for the pin"""
    hw = self.device.peripherals[port].registers['PIN_CNF%d' % bit]
    val = hw.rd()
    val &= ~(1 << 1)
    hw.wr(val)

  def set_input_disable(self, port, bit):
    """disable input for the pin"""
    hw = self.device.peripherals[port].registers['PIN_CNF%d' % bit]
    val = hw.rd()
    val |= 1 << 1
    hw.wr(val)

#-----------------------------------------------------------------------------
