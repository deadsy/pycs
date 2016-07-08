#-----------------------------------------------------------------------------
"""
Generic I2C Bit-Bang Driver
"""
#-----------------------------------------------------------------------------

import util

#-----------------------------------------------------------------------------
# I2C Exceptions


class Error(Exception):
  pass

_I2C_ERR_BUS = 'bus error'
_I2C_ERR_ADR = 'no response'
_I2C_ERR_NAK = 'missing ack'
_I2C_ERR_SLV = 'no slave data'

#-----------------------------------------------------------------------------

_help_read = (
    ('<adr> [n]', 'device address (hex)'),
    ('', 'n bytes to read (hex) - default is 1'),
)

_help_write = (
    ('<adr> <bytes>', 'device address (hex)'),
    ('', 'bytes to write (hex)'),
)

#-----------------------------------------------------------------------------


class i2c:
  """Generic I2C Bit-Bang Driver"""

  def __init__(self, io):
    self.io = io
    self.menu = (
      ('init', self.io.cmd_init),
      ('rd', self.cmd_rd, _help_read),
      ('scan', self.cmd_scan),
      ('wr', self.cmd_wr, _help_write),
    )

  def start(self):
    """
    Create start condition- SDA goes low while SCL is high.
    On Exit- SDA and SCL are held low.
    """
    self.io.scl_rel()
    self.io.sda_rel()
    # check that scl and sda are both high (no bus contention)
    if (not self.io.sda_rd()) or (not self.io.scl_rd()):
      raise Error, _I2C_ERR_BUS
    self.io.sda_lo()
    self.io.scl_lo()

  def stop(self):
    """
    Create stop condition- SDA goes high while SCL is high.
    On Exit- SDA and SCL are released.
    """
    self.io.scl_lo()
    self.io.sda_lo()
    self.io.scl_rel()
    self.io.sda_rel()

  def clock(self):
    """
    Clock SCL and read SDA at clock high.
    On Entry- SCL is held low.
    On Exit- SCL is held low, SDA =0/1 is returned.
    """
    self.io.scl_rel()
    # wait for any slave clock stretching
    delay = 4
    while (not self.io.scl_rd()) and (delay > 0):
      delay -= 1
    if delay == 0:
      self.stop()
      raise Error, _I2C_ERR_SLV
    val = self.io.sda_rd()
    self.io.scl_lo()
    return val

  def wr_byte(self, val):
    """
    Write a byte of data to the slave.
    On Entry- SCL is held low.
    On Exit- SDA is released, SCL is held low.
    """
    mask = 0x80
    while mask != 0:
      if val & mask:
        self.io.sda_rel()
      else:
        self.io.sda_lo()
      self.clock()
      mask >>= 1
    self.io.sda_rel()

  def rd_byte(self):
    """
    Read a byte from a slave.
    On Entry- SCL is held low.
    On Exit- SDA is released, SCL is held low
    """
    val = 0
    self.io.sda_rel()
    for i in range(8):
      val <<= 1
      val |= self.clock()
    return val

  def wr_ack(self):
    """
    Send an ack to the slave.
    """
    self.io.sda_lo()
    self.clock()
    self.io.sda_rel()

  def rd_ack(self):
    """
    Clock in the SDA level from the slave.
    Return: False = no ack, True = ack
    """
    self.io.sda_rel()
    return not self.clock()

  def rd(self, adr, n):
    """
    Read len bytes from device adr
    """
    # start a read cycle
    self.start()
    self.wr_byte(adr | 1)
    if not self.rd_ack():
      self.stop()
      raise Error, _I2C_ERR_ADR
    # read data
    buf = []
    for i in range(n):
      buf.append(self.rd_byte())
      # The last byte from the slave is not acked
      if i < (n - 1):
        self.wr_ack()
    self.stop()
    return buf

  def wr(self, adr, buf):
    """
    Write a buffer of bytes to device adr
    """
    # start a write cycle
    self.start()
    self.wr_byte(adr & ~1)
    if not self.rd_ack():
      self.stop()
      raise Error, _I2C_ERR_ADR
    # write data
    for i in range(len(buf)):
      self.wr_byte(buf[i])
      if not self.rd_ack():
        # no ack from slave
        self.stop()
        raise Error, _I2C_ERR_NAK
    self.stop()
    return True

  def adr_args(self, ui, args):
    adr = util.int_arg(ui, args[0], (0, 254), 16)
    if adr == None:
      return
    return adr & ~1

  def cmd_rd(self, ui, args):
    """read bytes from a device"""
    if util.wrong_argc(ui, args, (1, 2)):
      return
    adr = self.adr_args(ui, args)
    if adr == None:
      return
    n = 1
    if len(args) == 2:
      n = util.int_arg(ui, args[1], (1, 256), 16)
      if n == None:
        return
    try:
      self.io.cmd_init(ui, None)
      buf = self.rd(adr, n)
      plural = ('', 's')[len(buf) > 1]
      msg = '%s (%d byte%s)' % (' '.join(['%02x' % val for val in buf]), len(buf), plural)
    except Error, e:
      msg = e
    ui.put('0x%02x: %s\n' % (adr, msg))

  def cmd_wr(self, ui, args):
    """write bytes to a device"""
    if len(args) < 2:
      ui.put(util.bad_argc)
      return
    adr = self.adr_args(ui, args)
    if adr == None:
      return
    buf = []
    for arg in args[1:]:
      val = util.int_arg(ui, arg, (0, 255), 16)
      if val == None:
        return
      buf.append(val)
    try:
      self.io.cmd_init(ui, None)
      self.wr(adr, buf)
      plural = ('', 's')[len(buf) > 1]
      msg = '%s (%d byte%s)' % (' '.join(['%02x' % val for val in buf]), len(buf), plural)
    except Error, e:
      msg = e
    ui.put('0x%02x: %s\n' % (adr, msg))

  def cmd_scan(self, ui, args):
    """scan for i2c devices"""
    self.io.cmd_init(ui, None)
    found = []
    for adr in range(0, 255, 2):
      try:
        self.rd(adr, 1)
        found.append(adr)
        msg = 'device found'
      except Error, e:
        msg = e
      ui.put('0x%02x: %s\n' % (adr, msg))
    if found:
      ui.put('\ndevices at: %s\n' % ' '.join(['0x%02x' % adr for adr in found]))
    else:
      ui.put('\nno devices found\n')

#-----------------------------------------------------------------------------
