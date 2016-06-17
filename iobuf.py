# ----------------------------------------------------------------------------
"""
Input/Output Buffer Objects
Stateful objects used to produce/consume data from JTAG devices
"""
# ----------------------------------------------------------------------------

import sys
import string
import struct
import hashlib

sys.path.append('./darm/darm-master')
import darm
import util

# ----------------------------------------------------------------------------

printable = string.letters + string.digits + string.punctuation + ' '

# ----------------------------------------------------------------------------

class arm_disassemble:
  """disassemble incoming data into ARM instructions"""

  def __init__(self, ui, adr):
    self.ui = ui
    self.pc = adr
    self.state = 'thumb'

  def emit_thumb(self, opcode):
    """16 bit thumb instructions"""
    da = darm.disasm_thumb(opcode)
    s = '?'
    if da:
      s = str(da)
    self.ui.put('%08x: %04x       %s\n' % (self.pc, opcode, s))
    self.pc += 2

  def emit_thumb2(self, opcode):
    """32 bit thumb instructions"""
    da = darm.disasm_thumb2(opcode)
    s = '?'
    if da:
      s = str(da)
    self.ui.put('%08x: %04x %04x  %s\n' % (self.pc, opcode >> 16, opcode & 0xffff, s))
    self.pc += 4

  def emit16(self, x):
    if self.state == 'thumb':
      if ((x & 0xe000) == 0xe000) and (x & 0x1800):
        # this is a thumb2 opcode we need 32 bits
        self.save_x = x
        self.state = 'thumb2'
      else:
        # this is a thumb opcode
        self.emit_thumb(x)
    elif self.state == 'thumb2':
      self.emit_thumb2((self.save_x << 16) | x)
      # back to 16 bit mode
      self.state = 'thumb'
    else:
      assert False

  def write(self, data):
    self.emit16(data & 0xffff)
    self.emit16(data >> 16)

#-----------------------------------------------------------------------------

class write_file(object):

  def __init__(self, ui, name, size, mode = 'le'):
    self.ui = ui
    self.f = open(name, 'wb')
    self.n = 0
    self.fmt16 = ('>H', '<H')[mode == 'le']
    self.fmt32 = ('>L', '<L')[mode == 'le']
    # display output
    self.ui.put('writing to %s ' % name)
    self.progress = util.progress(ui, 8, size)

  def close(self):
    self.f.close()
    self.progress.erase()
    self.ui.put('done\n')

  def wr32(self, val):
    self.f.write(struct.pack(self.fmt32, val))
    self.n += 4
    self.progress.update(self.n)

  def wr16(self, val):
    self.f.write(struct.pack(self.fmt16, val))
    self.n += 2
    self.progress.update(self.n)

  def wr8(self, val):
    self.f.write(struct.pack('B', val))
    self.n += 1
    self.progress.update(self.n)

#-----------------------------------------------------------------------------

class read_file(object):

  def __init__(self, ui, name, size, mode = 'le'):
    self.ui = ui
    self.f = open(name, 'rb')
    self.n = 0
    self.fmt16 = ('>H', '<H')[mode == 'le']
    self.fmt32 = ('>L', '<L')[mode == 'le']
    # display output
    self.ui.put('reading from %s ' % name)
    self.progress = util.progress(ui, 8, size)

  def close(self):
    self.f.close()
    self.progress.erase()
    self.ui.put('done\n')

  def rd32(self):
    val = self.f.read(4)
    n = len(val)
    if n != 4:
      val = ''.join([val, '\xff' * (4 - n)])
    self.n += 4
    self.progress.update(self.n)
    return struct.unpack(self.fmt32, val)[0]

  def rd16(self):
    val = self.f.read(2)
    n = len(val)
    if n != 2:
      val = ''.join([val, '\xff' * (2 - n)])
    self.n += 2
    self.progress.update(self.n)
    return struct.unpack(self.fmt16, val)[0]

  def rd8():
    val = self.file.read(1)
    n = len(val)
    if n == 0:
      val = '\xff'
    self.n += 1
    self.progress.update(self.n)
    return struct.unpack('B', val)[0]

#-----------------------------------------------------------------------------

class data_buffer(object):

  def __init__(self, width, data = None):
    self.width = width
    self.buf = []
    if data:
      self.buf = [util.mask_val(x, self.width) for x in data]
    self.wr_idx = len(self.buf)
    self.rd_idx = 0

  def copy(self):
    """return a copy of this buffer"""
    return data_buffer(self.width, self.buf)

  def read(self):
    """read from the data buffer"""
    val = self.buf[self.rd_idx]
    self.rd_idx += 1
    return val

  def write(self, val):
    """write to the data buffer"""
    val = util.mask_val(val, self.width)
    if self.wr_idx == len(self.buf):
      # append to the buffer
      self.buf.append(val)
      self.wr_idx += 1
    elif self.wr_idx < len(self.buf):
      # replace existing content
      self.buf[self.wr_idx] = val
    else:
      assert False, 'buffer write error: more than 1 off the end'

  def wr32(self, val):
    assert self.width == 32, 'width is not 32 bits'
    self.write(val)

  def convert8(self, mode):
    """convert the buffer to 8 bit values"""
    if self.width == 32:
      new_buf = []
      for x in self.buf:
        if mode == 'be':
          # big endian conversion
          new_buf.append((x >> 24) & 255)
          new_buf.append((x >> 16) & 255)
          new_buf.append((x >> 8) & 255)
          new_buf.append(x & 255)
        else:
          # little endian conversion
          new_buf.append(x & 255)
          new_buf.append((x >> 8) & 255)
          new_buf.append((x >> 16) & 255)
          new_buf.append((x >> 24) & 255)
      self.buf = new_buf
    elif self.width == 16:
      new_buf = []
      for x in self.buf:
        if mode == 'be':
          # big endian conversion
          new_buf.append((x >> 8) & 255)
          new_buf.append(x & 255)
        else:
          # little endian conversion
          new_buf.append(x & 255)
          new_buf.append((x >> 8) & 255)
      self.buf = new_buf
    elif self.width == 8:
      # nothing to do
      return
    else:
      assert False, 'conversion error: width %d' % self.width
    # reset the buffer indices
    self.wr_idx = len(self.buf)
    self.rd_idx = 0
    self.width = 8

  def convert16(self, mode):
    """convert the buffer to 16 bit values"""
    if self.width == 32:
      new_buf = []
      for x in self.buf:
        if mode == 'be':
          # big endian conversion
          new_buf.append((x >> 16) & 0xffff)
          new_buf.append(x & 0xffff)
        else:
          # little endian conversion
          new_buf.append(x & 0xffff)
          new_buf.append((x >> 16) & 0xffff)
      self.buf = new_buf
    elif self.width == 16:
      # nothing to do
      return
    elif self.width == 8:
      assert False, 'TODO: unsupported conversion from 8 to 16 bits'
    else:
      assert False, 'conversion error: width %d' % self.width
    # reset the buffer indices
    self.wr_idx = len(self.buf)
    self.rd_idx = 0
    self.width = 16

  def convert32(self, mode):
    """convert the buffer to 32 bit values"""
    if self.width == 32:
      # nothing to do
      return
    elif self.width == 16:
      assert False, 'TODO: unsupported conversion from 16 to 32 bits'
    elif self.width == 8:
      # round up to a multiple of 4 bytes
      n = (4 - (len(self.buf) & 3)) & 3
      self.buf.extend((0,) * n)
      new_buf = []
      for i in range(0, len(self.buf), 4):
        if mode == 'be':
          # big endian conversion
          val = ((self.buf[i] << 24) |
                 (self.buf[i+1] << 16) |
                 (self.buf[i+2] << 8) |
                 (self.buf[i+3]))
        else:
          # little endian conversion
          val = (self.buf[i] |
                 (self.buf[i+1] << 8) |
                 (self.buf[i+2] << 16) |
                 (self.buf[i+3] << 24))
        new_buf.append(val)
      self.buf = new_buf
    else:
      assert False, 'conversion error: width %d' % self.width
    # reset the buffer indices
    self.wr_idx = len(self.buf)
    self.rd_idx = 0
    self.width = 32

  def convert(self, width, mode):
    if width == 8:
      self.convert8(mode)
    elif width == 16:
      self.convert16(mode)
    elif width == 32:
      self.convert32(mode)
    else:
      assert False, 'bad width'

  def endian_swap(self):
    """swap the endian-ness of all values"""
    if self.width == 32:
      self.buf = [util.swap32(x) for x in self.buf]
    elif self.width == 16:
      self.buf = [util.swap16(x) for x in self.buf]
    elif self.width == 8:
      # nothing to do
      return
    else:
      assert False, 'endian swap error: width %d' % self.width

  def md5(self, mode):
    """return an md5 hash of the buffer"""
    x = self.copy()
    x.convert8(mode)
    m = hashlib.md5()
    m.update(''.join([chr(b) for b in x.buf]))
    return m.hexdigest()

  def ascii_str(self):
    """return an ascii string representing an 8-bit buffer"""
    assert self.width == 8, 'width must be 8 bits'
    return ''.join([('.', chr(b))[chr(b) in printable] for b in self.buf])

  def __str__(self):
    """return a string for the buffer values"""
    fmt = '%%0%dx' % (self.width / 4)
    return ' '.join([fmt % x for x in self.buf])

#-----------------------------------------------------------------------------
