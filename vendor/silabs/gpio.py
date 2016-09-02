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

class drv(object):
  """GPIO driver for silabs devices"""

  def __init__(self, device, cfg = None):
    self.cfg = cfg
    self.hw = device.GPIO
    self.ports = ('A','B','C','D','E','F')

  def __status(self, port):
    """return a status string for the named gpio port"""
    s = []
    for i in range(16):
      # standard pin name
      pin_name = 'P%s%d' % (port, i)
      # target name
      tgt_name = ''
      # mode for this pin
      mode_name = 'i'
      val_name = '%d' % self.rd_input(port, i)
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
