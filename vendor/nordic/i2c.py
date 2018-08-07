#-----------------------------------------------------------------------------
"""
I2C Driver for Nordic Chips

Notes:

1) At the moment this is some glue between a generic bit banged i2c driver
and the gpio API.

2) The scl/sda lines are pulled up.
1 -> gpio as input, line is pulled high
0 -> gpio as 0 output, line is driven low

"""
#-----------------------------------------------------------------------------

class bitbang(object):
  """glue layer between bit banged i2c and the gpio pins"""

  def __init__(self, gpio, scl, sda):
    self.gpio = gpio
    (port, bit) = self.gpio.pin_arg(scl)
    self.scl_port = port
    self.scl_bit = bit
    (port, bit) = self.gpio.pin_arg(sda)
    self.sda_port = port
    self.sda_bit = bit
    self.hw_init = False

  def cmd_init(self, ui, args):
    """initialise i2c hardware"""
    if self.hw_init:
      return
    self.gpio.cmd_init(ui, args)
    ui.put('i2c init: ok\n')
    self.hw_init = True

  def sda_lo(self):
    """drive sda low"""
    self.gpio.set_dirn_out(self.sda_port, self.sda_bit)

  def sda_rel(self):
    """release sda"""
    self.gpio.set_dirn_in(self.sda_port, self.sda_bit)

  def sda_rd(self):
    """sda read"""
    return self.gpio.rd_input(self.sda_port, self.sda_bit)

  def scl_lo(self):
    """drive scl low"""
    self.gpio.set_dirn_out(self.scl_port, self.scl_bit)

  def scl_rel(self):
    """release scl"""
    self.gpio.set_dirn_in(self.scl_port, self.scl_bit)

  def scl_rd(self):
    """scl read"""
    return self.gpio.rd_input(self.scl_port, self.scl_bit)

#-----------------------------------------------------------------------------
