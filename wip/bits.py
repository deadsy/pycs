#-----------------------------------------------------------------------------
"""

Bit Buffers

Notes:

1. Represents bit buffers with Python's arbitrary length integers.

2. The least signifcant bit of the internal value is bit 0.
   The transmit order is right to left (as per the string representation).

3. In the bitstream "head" bits are taken to be before "tail" bits.

4. tail bits (tx/rx last).... body ..... head bits (tx/rx first)

"""
#-----------------------------------------------------------------------------

import random

#-----------------------------------------------------------------------------

class bits(object):
  """bit buffer object"""

  def __init__(self):
    self.val = 0
    self.n = 0

  def tail(self, b):
    """add a bit buffer to the tail"""
    self.val |= b.val << self.n
    self.n += b.n
    return self

  def tail0(self, n):
    """add zero bits to the tail"""
    self.n += n
    return self

  def tail1(self, n):
    """add one bits to the tail"""
    x = (1 << n) - 1
    self.val = (x << self.n) | self.val
    self.n += n
    return self

  def head0(self, n):
    """add zero bits to the head"""
    self.val <<= n
    self.n += n
    return self

  def head(self, b):
    """add a bit buffer to the head"""
    self.val = (self.val << b.n) | b.val
    self.n += b.n
    return self

  def drop_head(self, n):
    """remove n bits from the head"""
    if n < self.n:
      self.val >>= n
      self.n -= n
    else:
      self.n = 0
      self.val = 0
    return self

  def drop_tail(self, n):
    """remove n bits from the tail"""
    if n < self.n:
      self.val &= (1 << (self.n - n)) - 1
      self.n -= n
    else:
      self.n = 0
      self.val = 0
    return self

  def copy(self):
    """return a copy of this bit buffer"""
    x = bits()
    x.val = self.val
    x.n = self.n
    return x

  def get_bytes(self):
    """return a byte array for the bit buffer"""
    n = (self.n + 7) >> 3
    return [(self.val >> (i * 8)) & 0xff for i in range(n)]

  def set_bytes(self, buf, n):
    """set a bit buffer from a byte array"""
    self.val = 0
    for i in range(len(buf) - 1, -1, -1):
      self.val <<= 8
      self.val |= buf[i]
    self.n = n
    return self

  def split(self, fmt):
    """split a bit buffer using the number of bits in the fmt tuple"""
    x = []
    val = self.val
    for n in fmt:
      mask = (1 << n) - 1
      x.append(val & mask)
      val >>= n
    return x

  def bit_str(self):
    """return a 0/1 bit string"""
    s = []
    for i in range(self.n - 1, -1, -1):
      s.append(('0', '1')[self.val & (1 << i) != 0])
    return ''.join(s)

  def __str__(self):
    return '(%d) %s' % (self.n, self.bit_str())

  def __len__(self):
    return self.n

  def __eq__(self, x):
    return (self.n == x.n) and (self.val == x.val)

  def __ne__(self, x):
    return not ((self.n == x.n) and (self.val == x.val))

#-----------------------------------------------------------------------------

def from_tuple(t):
  """return a bit buffer from a 1/0 tuple, string or list"""
  val = 0
  for b in t:
    val <<= 1
    if b == 1 or b == '1':
      val |= 1
  x = bits()
  x.n = len(t)
  x.val = val
  return x

def from_random(n):
  """return a bit buffer with n random 0/1 bits"""
  return from_tuple([random.randint(0, 1) for i in range(n)])

def from_val(val, n):
  x = bits()
  x.val = val & ((1 << n) - 1)
  x.n = n
  return x

def zeroes(n):
  """return n zero bits"""
  return bits().tail0(n)

def ones(n):
  """return n one bits"""
  return bits().tail1(n)

def null():
  """return an empty bit buffer"""
  return bits()

#-----------------------------------------------------------------------------
