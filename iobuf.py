# ----------------------------------------------------------------------------
"""
Input/Output Buffer Objects
Stateful objects used to produce/consume data from JTAG devices
"""
# ----------------------------------------------------------------------------

import sys
import string
import struct
import util

sys.path.append('./darm/darm-master')
import darm

# ----------------------------------------------------------------------------

_shifts8 = (0,)
_shifts32_be = (24, 16, 8, 0)
_shifts32_le = (0, 8, 16, 24)
_shifts64 = (56, 48, 40, 32, 24, 16, 8, 0)

_display32 = 'address   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F\n'
_display64 = 'address           0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F\n'

printable = string.letters + string.digits + string.punctuation + ' '

# ----------------------------------------------------------------------------

class arm_disassemble:
  """disassemble incoming data into ARM instructions"""

  def __init__(self, ui, adr):
    self.ui = ui
    self.pc = adr
    self.format = '%08x %08x: %s\n'

  def emit(self, opcode):
    da = darm.disasm_armv7(opcode)
    da_str = '?'
    if da:
      da_str = str(da)
    self.ui.put(self.format % (self.pc, opcode, da_str))
    self.pc += 4

  def write(self, data):
    """output the disassembled instructions to the console"""
    self.emit(data)

# ----------------------------------------------------------------------------

class to_display:
  """write data as a memory dump to the display"""

  def __init__(self, width, ui, adr, le=False):
    self.width = width
    self.ui = ui
    self.base = adr
    self.adr = adr
    self.inc = self.width >> 3
    if self.width == 8:
      self.shifts = _shifts8
      self.ui.put(_display32)
      self.format = '%08x: %s'
    elif self.width == 32:
      self.shifts = (_shifts32_be, _shifts32_le)[le]
      self.ui.put(_display32)
      self.format = '%08x: %s'
    elif self.width == 64:
      self.shifts = _shifts64
      self.ui.put(_display64)
      self.format = '%016x: %s'

  def byte2char(self, bytes):
    """convert a set of bytes into printable characters"""
    char_str = [('.', chr(b))[chr(b) in printable] for b in bytes]
    return ''.join(char_str)

  def write(self, data):
    """output the memory dump to the console"""
    bytes = [((data >> s) & 0xff) for s in self.shifts]
    byte_str = ''.join(['%02x ' % b for b in bytes])
    posn = (self.adr - self.base) & 0x0f
    if posn == 0:
      self.ascii = self.byte2char(bytes)
      self.ui.put(self.format % (self.adr, byte_str))
    elif (posn + self.inc) == 16:
      ascii_str = ''.join([self.ascii, self.byte2char(bytes)])
      self.ui.put('%s %s\n' % (byte_str, ascii_str))
    else:
      self.ascii = ''.join([self.ascii, self.byte2char(bytes)])
      self.ui.put('%s' % byte_str)
    self.adr += self.inc

# ----------------------------------------------------------------------------

class to_file:
  """write data to a file"""

  def __init__(self, width, ui, name, nmax, le = False):
    self.width = width
    self.ui = ui
    self.file = open(name, 'wb')
    self.n = 0
    # endian converion
    self.convert = util.identity
    if le:
      if self.width == 32:
        self.convert = util.btol32
      elif self.width == 64:
        self.convert = util.btol64
    # display output
    self.ui.put('writing to %s ' % name)
    self.progress = util.progress(ui, 7, nmax)

  def close(self):
    self.file.close()
    self.progress.erase()
    self.ui.put('done\n')

  def write(self, data):
    """output the memory dump to a file"""
    data = self.convert(data)
    if self.width == 64:
      self.file.write(struct.pack('>Q', data))
    elif self.width == 32:
      self.file.write(struct.pack('>L', data))
    else:
      self.file.write(struct.pack('B', data))
    self.n += 1
    self.progress.update(self.n)

#-----------------------------------------------------------------------------

class data_buffer(object):

  def __init__(self, width, data = None):
    self.width = width
    self.buf = []
    if data:
      self.buf = [util.mask_val(x, self.width) for x in data]
    self.wr_idx = len(self.buf)
    self.rd_idx = 0

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
      assert False, 'TODO: unsupported conversion from 16 to 32 bits'
    elif self.width == 8:
      # nothing to do
      return
    else:
      assert False, 'conversion error: width %d' % self.width
    # reset the buffer indices
    self.wr_idx = len(self.buf)
    self.rd_idx = 0
    self.width = 8

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

#-----------------------------------------------------------------------------
