#-----------------------------------------------------------------------------
"""
GPIO Driver for Microchip ATSAM Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

"""
#-----------------------------------------------------------------------------

import util

#-----------------------------------------------------------------------------

# PINCFG bits
PINCFG_DRVSTR = 1 << 6  # Output Driver Strength Selection
PINCFG_PULLEN = 1 << 2  # Pull Enable
PINCFG_INEN = 1 << 1    # Input Enable
PINCFG_PMUXEN = 1 << 0  # Peripheral Multiplexer Enable

#-----------------------------------------------------------------------------

class drv(object):
  """GPIO driver for Microchip ATSAM devices"""

  def __init__(self, device, cfg = None):
    self.device = device
    self.cfg = cfg
    self.hw_init = False
    # work out the pin to name mapping from the configuration
    self.pin2name = {}
    for (pin, mode, name) in self.cfg:
      self.pin2name[pin] = name

  def __status(self, port, bit):
    """return a status string for the named gpio port and bit"""
    # standard pin name
    pin_name = '%s%02d' % (port, bit)
    # target name
    tgt_name = self.pin2name.get(pin_name, None)
    val_name = ''
    # gpio/mux mode
    cfg = self.rd_cfg(port, bit)
    if cfg & (1 << 0) != 0:
      # pin is muxed
      mode_name = 'mux_%d' % self.rd_mux(port, bit)
    else:
      dirn = self.rd_dir(port)
      if dirn & (1 << bit) != 0:
        # pin is an output
        mode_name = 'out'
        val_name = '%d' % self.rd_output(port, bit)
      else:
        if cfg & (1 << 1) != 0:
          # pin is an input
          mode_name = 'in'
          val_name = '%d' % self.rd_input(port, bit)
        else:
          # pin is disabled
          mode_name = 'x'
    return (pin_name, mode_name, val_name, tgt_name)

  # The following functions are the common API

  def cmd_init(self, ui, args):
    """initialise gpio hardware"""
    if self.hw_init:
      return
    # enable each gpio port in the configuration set
    ports = {}
    for (pin, mode, name) in self.cfg:
      (port, bit) = self.pin_arg(pin)
      if mode == 'i':
        self.set_dir_in(port, bit)
        self.wr_cfg(port, bit, PINCFG_INEN)
      elif mode == 'i_pu':
        self.set_dir_in(port, bit)
        self.wr_cfg(port, bit, PINCFG_INEN | PINCFG_PULLEN)
        self.set_bit(port, bit)
      elif mode == 'i_pd':
        self.set_dir_in(port, bit)
        self.wr_cfg(port, bit, PINCFG_INEN | PINCFG_PULLEN)
        self.clr_bit(port, bit)
      elif mode == 'o':
        self.set_dir_out(port, bit)
        self.wr_cfg(port, bit, 0)
      elif mode == 'o_s':
        self.set_dir_out(port, bit)
        self.wr_cfg(port, bit, PINCFG_DRVSTR)
    self.hw_init = True
    ui.put('gpio init: ok\n')

  def pin_arg(self, name):
    """convert a standard pin name into a port/bit tuple or None"""
    if len(name) > 4:
      return None
    name = name.upper()
    if not name.startswith('P'):
      return None
    port = name[:2]
    try:
      pin = int(name[2:])
    except:
      return None
    if pin > 31:
      return None
    return (port, pin)

  def rd_output(self, port, bit = None):
    """read the output value"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['OUT%d' % n]
    val = hw.rd()
    if bit is None:
      return val
    return (val >> (bit & 31)) & 1

  def rd_input(self, port, bit = None):
    """read the input value"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['IN%d' % n]
    val = hw.rd()
    if bit is None:
      return val
    return (val >> (bit & 31)) & 1

  def wr(self, port, val):
    """write the output value"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['OUT%d' % n]
    hw.wr(val)

  def set_bit(self, port, bit):
    """set an output bit"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['OUTSET%d' % n]
    hw.wr(1 << (bit & 31))

  def clr_bit(self, port, bit):
    """clear an output bit"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['OUTCLR%d' % n]
    hw.wr(1 << (bit & 31))

  def __str__(self):
    s = []
    for (pin, _, _) in self.cfg:
      (port, bit) = self.pin_arg(pin)
      s.append(self.__status(port, bit))
    return util.display_cols(s)

  # The following functions are Microchip ATSAM specific
  # They can be called from target code - but not from generic drivers.

  def rd_dir(self, port):
    """read the port direction"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['DIR%d' % n]
    return hw.rd()

  def rd_cfg(self, port, bit):
    """read the pin configuration"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['PINCFG%d_%d' % (n,bit & 31)]
    return hw.rd8()

  def wr_cfg(self, port, bit, val):
    """write the pin configuration"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['PINCFG%d_%d' % (n,bit & 31)]
    return hw.wr8(val & 0xff)

  def rd_mux(self, port, bit):
    """read the pin mux setting"""
    n = {'PA':0, 'PB':1}[port]
    bit &= 31
    hw = self.device.peripherals['PORT'].registers['PMUX%d_%d' % (n, bit >> 1)]
    val = hw.rd8()
    if bit & 1 != 0:
      val >>= 4
    return val & 15

  def set_dir_in(self, port, bit):
    """set the pin direction as an input"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['DIRCLR%d' % n]
    hw.wr(1 << (bit & 31))

  def set_dir_out(self, port, bit):
    """set the pin direction as an output"""
    n = {'PA':0, 'PB':1}[port]
    hw = self.device.peripherals['PORT'].registers['DIRSET%d' % n]
    hw.wr(1 << (bit & 31))

#-----------------------------------------------------------------------------
