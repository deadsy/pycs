#-----------------------------------------------------------------------------
"""
I2C Driver for ST Chips

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

  def pin_init(self, port, bit):
    """setup the gpio for an i2c pin"""
    # normally the pin is an input with a pull-up
    self.gpio.set_mode(port, bit, 'i')
    self.gpio.set_pupd(port, bit, 'pu')
    # setting the pin to an output drives it low
    self.gpio.clr_bit(port, bit)
    self.gpio.set_otype(port, bit, 'pp')
    self.gpio.set_ospeed(port, bit, 'l')

  def cmd_init(self, ui, args):
    """initialise i2c hardware"""
    if self.hw_init:
      return
    # do a gpio init - there may be some device gpio lines that need to be set/reset
    self.gpio.cmd_init(ui, args)
    self.pin_init(self.scl_port, self.scl_bit)
    self.pin_init(self.sda_port, self.sda_bit)
    ui.put('i2c init: ok\n')
    self.hw_init = True

  def sda_lo(self):
    """drive sda low"""
    self.gpio.set_mode(self.sda_port, self.sda_bit, 'o')

  def sda_rel(self):
    """release sda"""
    self.gpio.set_mode(self.sda_port, self.sda_bit, 'i')

  def sda_rd(self):
    """sda read"""
    return self.gpio.rd_input(self.sda_port, self.sda_bit)

  def scl_lo(self):
    """drive scl low"""
    self.gpio.set_mode(self.scl_port, self.scl_bit, 'o')

  def scl_rel(self):
    """release scl"""
    self.gpio.set_mode(self.scl_port, self.scl_bit, 'i')

  def scl_rd(self):
    """scl read"""
    return self.gpio.rd_input(self.scl_port, self.scl_bit)

#-----------------------------------------------------------------------------
