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
    self.hw_init = False
    # work out the pin to name mapping from the configuration
    self.pin2name = {}
    for (pin, sense, drive, pupd, in_enable, dirn, name) in self.cfg:
      self.pin2name[pin] = name

  def __status(self, port, bit):
    """return a status string for the named gpio port and bit"""
    hw = self.device.peripherals[port]
    # standard pin name
    pin_name = '%s.%d' % (port, bit)
    # target name
    tgt_name = self.pin2name.get(pin_name, None)
    # configuration for this pin
    conf = hw.registers['PIN_CNF%d' % bit]
    mode_name = conf.DIR.field_name(conf.rd())
    if mode_name == 'Input':
      mode_name = 'i'
      val_name = '%d' % self.rd_input(port, bit)
    elif mode_name == 'Output':
      mode_name = 'o'
      val_name = '%d' % self.rd_output(port, bit)
    return (pin_name, mode_name, val_name, tgt_name)

  # The following functions are the common API

  def cmd_init(self, ui, args):
    """initialise gpio hardware"""
    if self.hw_init:
      return
    for (pin, sense_mode, drive_mode, pull_mode, input_mode, dir_mode, name) in self.cfg:
      (port, bit) = self.pin_arg(pin)
      self.set_dir(port, bit, dir_mode)
      self.set_input(port, bit, input_mode)
      self.set_pull(port, bit, pull_mode)
      self.set_drive(port, bit, drive_mode)
      self.set_sense(port, bit, sense_mode)
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
    for (pin, _, _, _, _, _, _) in self.cfg:
      (port, bit) = self.pin_arg(pin)
      s.append(self.__status(port, bit))
    return util.display_cols(s)

  # The following functions are Nordic specific
  # They can be called from target code - but not from generic drivers.

  def set_dir(self, port, bit, mode):
    """set the DIR field of the PIN_CNF[bit] register"""
    if mode is None:
      return
    hw = self.device.peripherals[port].registers['PIN_CNF%d' % bit]
    val = hw.rd()
    val &= ~(1 << 0)
    val |= {'i':(0 << 0), 'o':(1 << 0)}[mode]
    hw.wr(val)

  def set_input(self, port, bit, mode):
    """set the INPUT field of the PIN_CNF[bit] register"""
    if mode is None:
      return
    hw = self.device.peripherals[port].registers['PIN_CNF%d' % bit]
    val = hw.rd()
    val &= ~(1 << 1)
    val |= {'connect':(0 << 1), 'disconnect':(1 << 1)}[mode]
    hw.wr(val)

  def set_pull(self, port, bit, mode):
    """set the PULL field of the PIN_CNF[bit] register"""
    if mode is None:
      return
    hw = self.device.peripherals[port].registers['PIN_CNF%d' % bit]
    val = hw.rd()
    val &= ~(3 << 2)
    val |= {'disable':(0 << 2), 'pd':(1 << 2), 'pu':(3 << 2)}[mode]
    hw.wr(val)

  def set_drive(self, port, bit, mode):
    """set the DRIVE field of the PIN_CNF[bit] register"""
    if mode is None:
      return
    hw = self.device.peripherals[port].registers['PIN_CNF%d' % bit]
    val = hw.rd()
    val &= ~(7 << 8)
    val |= {'s0s1':(0 << 8),
            'h0s1':(1 << 8),
            's0h1':(2 << 8),
            'h0h1':(3 << 8),
            'd0s1':(4 << 8),
            'd0h1':(5 << 8),
            's0d1':(6 << 8),
            'h0d1':(7 << 8),
            }[mode]
    hw.wr(val)

  def set_sense(self, port, bit, mode):
    """set the SENSE field of the PIN_CNF[bit] register"""
    if mode is None:
      return
    hw = self.device.peripherals[port].registers['PIN_CNF%d' % bit]
    val = hw.rd()
    val &= ~(3 << 16)
    val |= {'disable':(0 << 16), 'hi':(2 << 16), 'lo':(3 << 16)}[mode]
    hw.wr(val)

#-----------------------------------------------------------------------------
