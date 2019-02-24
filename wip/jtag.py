#------------------------------------------------------------------------------
"""
JTAG Chain Controller
"""
#------------------------------------------------------------------------------

import bits
import idcode

#------------------------------------------------------------------------------

_max_devices = 6
_flush_size = _max_devices * 32
_idcode_length = 32

#------------------------------------------------------------------------------

class Error(Exception):
  """JTAG chain error"""
  pass

#------------------------------------------------------------------------------
# operations on chain specifications

def chspec_irlen(chspec, idx):
  """return the total ir length before device at idx position"""
  irlen = 0
  for (i, d) in enumerate(chspec):
    if i < idx:
      irlen += d[0]
  return irlen

def chspec_total_irlen(chspec):
  """return the total ir length in the chain specification"""
  return chspec_irlen(chspec, len(chspec))

#------------------------------------------------------------------------------

class device(object):
  """A device on the JTAG chain"""

  def __init__(self, idx, chain, chspec):
    self.idx = idx
    self.chain = chain
    (irlen, idcode, name) = chspec[idx]
    self.irlen = irlen # ir bit length of this device
    self.idcode = idcode # idcode of device
    self.name = name # name of the device
    self.devs_before = idx # devices before this device
    self.devs_after = len(chspec) - idx - 1 # devices after this device
    self.irlen_before = chspec_irlen(chspec, idx) # ir bits before this device
    self.irlen_after = chspec_total_irlen(chspec) - self.irlen_before - self.irlen # ir bits after this device

  def wr_ir(self, wr):
    """write to IR for a device"""
    # place other devices into bypass mode (ir = all 1's)
    tdi = bits.ones(self.irlen_before).tail(wr).tail1(self.irlen_after)
    self.chain.driver.scan_ir(tdi)

  def rw_ir(self, wr):
    """read/write IR for a device"""
    tdi = bits.ones(self.irlen_before).tail(wr).tail1(self.irlen_after)
    tdo = bits.null()
    self.chain.driver.scan_ir(tdi, tdo)
    # strip the ir bits from the other devices
    tdo.drop_head(self.irlen_before)
    tdo.drop_tail(self.irlen_after)
    return tdo

  def wr_dr(self, wr):
    """write to DR for a device"""
    # other devices are assumed to be in bypass mode (dr length = 1)
    tdi = bits.ones(self.devs_before).tail(wr).tail1(self.devs_after)
    self.chain.driver.scan_dr(tdi)

  def rw_dr(self, wr):
    """read/write DR for a device"""
    tdi = bits.ones(self.devs_before).tail(wr).tail1(self.devs_after)
    tdo = bits.null()
    self.chain.driver.scan_dr(tdi, tdo)
    # strip the dr bits from the bypassed devices
    tdo.drop_head(self.devs_before)
    tdo.drop_tail(self.devs_after)
    return tdo

  def test_ir_capture(self):
    """test the IR capture result"""
    # write all-1s to the IR
    rd = self.rw_ir(bits.ones(self.irlen))
    val = rd.split((self.irlen,))[0]
    # the lowest 2 bits should be "01"
    return val & 3 == 1

  def ir_survey(self):
    """return a string with all IR values and the DR lengths"""
    s = []
    for ir in range((1 << self.irlen)):
      self.wr_ir(bits.from_val(ir, self.irlen))
      try:
        n = self.chain.dr_length() - self.devs_after - self.devs_before
        s.append('ir %d drlen %d' % (ir, n))
      except:
        s.append('ir %d drlen unknown' % ir)
    return '\n'.join(s)

  def __str__(self):
    return 'idx %d %s irlen %d %s' % (self.idx, self.name, self.irlen, idcode.decode(self.idcode))

#------------------------------------------------------------------------------

class chain(object):
  """JTAG chain controller"""

  def __init__(self, driver, chspec):
    self.driver = driver
    self.device = []
    self.scan(chspec)

  def scan(self, chspec):
    """scan the jtag chain"""
    self.driver.tap_reset()
    self.n = self.num_devices()
    # sanity check the number of devices
    if len(chspec) != self.n:
      raise Error('expecting %d devices, found %d' % (len(chspec), self.n))
    self.irlen = self.ir_length()
    # sanity check the total ir length
    irlen = chspec_total_irlen(chspec)
    if irlen != self.irlen:
      raise Error('expecting irlen %d bits, found %d bits' % (irlen, self.irlen))
    # sanity check the device idcodes
    idcode = self.read_idcodes()
    for i, d in enumerate(chspec):
      if d[1] != idcode[i]:
        raise Error('expecting idcode 0x%08x at position %d, found 0x%08x' % (d[1], i, idcode[i]))
    # build the devices
    for i in range(len(chspec)):
      self.device.append(device(i, self, chspec))
    # test the IR capture value for all devices
    for d in self.device:
      if not d.test_ir_capture():
        raise Error('failed IR capture for idcode 0x%08x at position %d' % (d.idcode, d.idx))

  def read_idcodes(self):
    """return a tuple of idcodes for the JTAG chain"""
    # a TAP reset leaves the idcodes in the DR chain
    self.driver.tap_reset()
    tdi = bits.ones(self.n * _idcode_length)
    tdo = bits.null()
    self.driver.scan_dr(tdi, tdo)
    return tdo.split((_idcode_length,) * self.n)

  def chain_length(self, scan):
    """return the length of the JTAG chain"""
    tdo = bits.null()
    # build a 000...001000...000 flush buffer for tdi
    tdi = bits.zeroes(_flush_size).tail1(1).tail0(_flush_size)
    scan(tdi, tdo)
    # the first bits are junk
    tdo.drop_head(_flush_size)
    # work out how many bits tdo is behind tdi
    s = tdo.bit_str()
    s = s.lstrip('0')
    if len(s.replace('0', '')) != 1:
      raise Error('unexpected result from jtag chain, there should be a single 1')
    return len(s) - 1

  def dr_length(self):
    """return the length of the DR chain"""
    # Note: DR chain length is a function of current IR chain state
    return self.chain_length(self.driver.scan_dr)

  def ir_length(self):
    """return the length of the ir chain"""
    return self.chain_length(self.driver.scan_ir)

  def num_devices(self):
    """return the number of JTAG devices in the chain"""
    # put every device into bypass mode (IR = all 1's)
    self.driver.scan_ir(bits.ones(_flush_size))
    # now each DR is a single bit
    # the DR chain length is the number of devices
    return self.dr_length()

  def __str__(self):
    """return a string describing the jtag chain"""
    s = []
    s.append('JTAG chain irlen %d devices %d' % (self.irlen, self.n))
    s.extend([str(d) for d in self.device])
    return '\n'.join(s)

#------------------------------------------------------------------------------
