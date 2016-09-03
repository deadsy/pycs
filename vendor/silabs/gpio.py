#-----------------------------------------------------------------------------
"""
GPIO Driver for Silicon Labs Chips

Notes:

1) Instantiating this driver does not touch the hardware. No reads or writes.
We only access the hardware when the user wants to do something.

"""
#-----------------------------------------------------------------------------

import util

#-----------------------------------------------------------------------------

_modes = {
  0: 'disabled', # Input disabled. Pullup if DOUT is set
  1: 'in', # Input enabled. Filter if DOUT is set
  2: 'in/pull', # Input enabled. DOUT determines pull direction
  3: 'in/pull/filter', # Input enabled with filter. DOUT determines pull direction
  4: 'out/push-pull', # Push-pull output
  5: 'out/push-pull/drive', # Push-pull output with drive-strength set by DRIVEMODE
  6: 'out/wired-or', # Wired-or output
  7: 'out/wired-or/pull-down', # Wired-or output with pull-down
  8: 'out/wired-and', # Open-drain output
  9: 'out/wired-and/filter', # Open-drain output with filter
  10: 'out/wired-and/pull-up', # Open-drain output with pullup
  11: 'out/wired-and/pull-up/filter', #Open-drain output with filter and pullup
  12: 'out/wired-and/drive', #Open-drain output with drive-strength set by DRIVEMODE
  13: 'out/wired-and/filter', #Open-drain output with filter and drive-strength set by DRIVEMODE
  14: 'out/wired-and/drive/pull-up', #Open-drain output with pullup and drive-strength set by DRIVEMODE
  15: 'out/wired-and/drive/pull-up/filter', #Open-drain output with filter, pullup and drive-strength set by DRIVEMODE
}

#-----------------------------------------------------------------------------

class drv(object):
  """GPIO driver for silabs devices"""

  def __init__(self, device, cfg = None):
    self.cfg = cfg
    self.hw = device.GPIO
    self.ports = ('A','B','C','D','E','F')
    # work out the pin to name mapping from the configuration
    self.pin2name = {}
    for (pin, name) in self.cfg:
      self.pin2name[pin] = name

  def __status(self, port):
    """return a status string for the named gpio port"""
    s = []
    mode_l = self.hw.registers['P%s_MODEL' % port].rd()
    mode_h = self.hw.registers['P%s_MODEH' % port].rd()
    mode_val = (mode_h << 32) | mode_l
    for i in range(16):
      # standard pin name
      pin_name = 'P%s%d' % (port, i)
      # target name
      tgt_name = self.pin2name.get(pin_name, None)
      # mode for this pin
      pin_mode = (mode_val >> (i * 4)) & 0xf
      mode_name = _modes[pin_mode]
      if pin_mode == 0:
        val_name = 'x'
      elif pin_mode <= 3:
        val_name = '%d' % self.rd_input(port, i)
      else:
        val_name = '%d' % self.rd_output(port, i)
      s.append([pin_name, mode_name, val_name, tgt_name])
    return s

  # The following functions are the common API

  def cmd_init(self, ui, args):
    """initialise gpio hardware"""
    if self.hw_init:
      return
    # enable each gpio port in the configuration set

    self.hw_init = True
    ui.put('gpio init: ok\n')

  def pin_arg(self, name):
    """convert a standard pin name into a port/bit tuple or None"""
    if len(name) > 4:
      return None
    name = name.upper()
    if not name.startswith('P'):
      return None
    port = name[1]
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
    val = self.hw.registers['P%s_DOUT' % port].rd()
    if bit is None:
      return val
    return (val >> (bit & 15)) & 1

  def rd_input(self, port, bit = None):
    """read the input value"""
    val = self.hw.registers['P%s_DIN' % port].rd()
    if bit is None:
      return val
    return (val >> (bit & 15)) & 1

  def wr(self, port, val):
    """write the output value"""
    self.hw.registers['P%s_DOUT' % port].wr(val)

  def set_bit(self, port, bit):
    """set an output bit"""
    self.hw.registers['P%s_DOUTSET' % port].wr(1 << (bit & 15))

  def clr_bit(self, port, bit):
    """clear an output bit"""
    self.hw.registers['P%s_DOUTCLR' % port].wr(1 << (bit & 15))

  def __str__(self):
    s = []
    for p in self.ports:
      s.extend(self.__status(p))
    return util.display_cols(s)

#-----------------------------------------------------------------------------
