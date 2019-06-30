#-----------------------------------------------------------------------------
"""

NXP i.MX RT FlexSPI Controller

"""
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------

# opcodes

OPCODE_CMD_SDR = 0x01
OPCODE_CMD_DDR = 0x21
OPCODE_RADDR_SDR = 0x02
OPCODE_RADDR_DDR = 0x22
OPCODE_CADDR_SDR = 0x03
OPCODE_CADDR_DDR = 0x23
OPCODE_MODE1_SDR = 0x04
OPCODE_MODE1_DDR = 0x24
OPCODE_MODE2_SDR = 0x05
OPCODE_MODE2_DDR = 0x25
OPCODE_MODE4_SDR = 0x06
OPCODE_MODE4_DDR = 0x26
OPCODE_MODE8_SDR = 0x07
OPCODE_MODE8_DDR = 0x27
OPCODE_WRITE_SDR = 0x08
OPCODE_WRITE_DDR = 0x28
OPCODE_READ_SDR = 0x09
OPCODE_READ_DDR = 0x29
OPCODE_LEARN_SDR = 0x0a
OPCODE_LEARN_DDR = 0x2a
OPCODE_DATSZ_SDR = 0x0b
OPCODE_DATSZ_DDR = 0x2b
OPCODE_DUMMY_SDR = 0x0c
OPCODE_DUMMY_DDR = 0x2c
OPCODE_DUMMY_RWDS_SDR = 0x0d
OPCODE_DUMMY_RWDS_DDR = 0x2d
OPCODE_JMP_ON_CS = 0x1f
OPCODE_STOP = 0

opcode_names = {
  OPCODE_CMD_SDR: 'CMD_SDR',
  OPCODE_CMD_DDR: 'CMD_DDR',
  OPCODE_RADDR_SDR: 'RADDR_SDR',
  OPCODE_RADDR_DDR: 'RADDR_DDR',
  OPCODE_CADDR_SDR: 'CADDR_SDR',
  OPCODE_CADDR_DDR: 'CADDR_DDR',
  OPCODE_MODE1_SDR: 'MODE1_SDR',
  OPCODE_MODE1_DDR: 'MODE1_DDR',
  OPCODE_MODE2_SDR: 'MODE2_SDR',
  OPCODE_MODE2_DDR: 'MODE2_DDR',
  OPCODE_MODE4_SDR: 'MODE4_SDR',
  OPCODE_MODE4_DDR: 'MODE4_DDR',
  OPCODE_MODE8_SDR: 'MODE8_SDR',
  OPCODE_MODE8_DDR: 'MODE8_DDR',
  OPCODE_WRITE_SDR: 'WRITE_SDR',
  OPCODE_WRITE_DDR: 'WRITE_DDR',
  OPCODE_READ_SDR: 'READ_SDR',
  OPCODE_READ_DDR: 'READ_DDR',
  OPCODE_LEARN_SDR: 'LEARN_SDR',
  OPCODE_LEARN_DDR: 'LEARN_DDR',
  OPCODE_DATSZ_SDR: 'DATSZ_SDR',
  OPCODE_DATSZ_DDR: 'DATSZ_DDR',
  OPCODE_DUMMY_SDR: 'DUMMY_SDR',
  OPCODE_DUMMY_DDR: 'DUMMY_DDR',
  OPCODE_DUMMY_RWDS_SDR: 'DUMMY_RWDS_SDR',
  OPCODE_DUMMY_RWDS_DDR: 'DUMMY_RWDS_DDR',
  OPCODE_JMP_ON_CS: 'JMP_ON_CS',
  OPCODE_STOP: 'STOP',
}

# pads

PAD_X1 = 0
PAD_X2 = 1
PAD_X4 = 2
PAD_X8 = 3

pad_names = {
  PAD_X1: 'x1',
  PAD_X2: 'x2',
  PAD_X4: 'x4',
  PAD_X8: 'x8',
}

def opcode_decode(x):
  if x in opcode_names:
    return '%s' % opcode_names[x]
  return '%02x' % x

def op_decode(x):
  """return a string for the lut instruction code"""
  x &= 0xffff
  opcode = opcode_decode(x >> 10)
  pads = pad_names[(x >> 8) & 3]
  operand = x & 0xff
  return '%s %s %02x' % (opcode, pads, operand)

def op_encode(opcode, pads, operand):
  """encode a lut instruction code"""
  return ((opcode & 0x3f) << 10) | ((pads & 0x3) << 8) | (operand & 0xff)

#-----------------------------------------------------------------------------

class flexspi:
  def __init__(self, device):
    self.device = device
    self.hw = self.device.FLEXSPI
    self.menu = (
      ('info', self.cmd_info),
      ('init', self.cmd_init),
    )

  def lut_lock(self):
    """lock the lut access"""
    self.hw.LUTKEY.wr(0x5AF05AF0)
    self.hw.LUTCR.wr(1)

  def lut_unlock(self):
    """unlock the lut access"""
    self.hw.LUTKEY.wr(0x5AF05AF0)
    self.hw.LUTCR.wr(2)

  def lut_rd(self, i):
    """read a LUT regsister"""
    return self.hw.registers['LUT%d' % i].rd()

  def lut_wr(self, i, val):
    """write a LUT regsister"""
    self.lut_unlock()
    self.hw.registers['LUT%d' % i].wr(val)
    self.lut_lock()

  def lut_set(self, seq, ins, code):
    """set an opcode at the lut seq/ins location"""
    # read
    i = (seq << 2) + (ins >> 1)
    val = self.lut_rd(i)
    # modify
    if ins & 1:
      val = (val & 0x0000ffff) | (code << 16)
    else:
      val = (val & 0xffff0000) | code
    # write
    self.lut_wr(i, val)

  def cmd_info(self, ui, args):
    """display flexspi information"""
    for s in range(16):
      ui.put('sequence %d\n' % s)
      for i in range(4):
        x = self.hw.registers['LUT%d' % ((s * 4) + i)].rd()
        ui.put('ins %d: %s\n' % ((i * 2) + 0, op_decode(x & 0xffff)))
        ui.put('ins %d: %s\n' % ((i * 2) + 1, op_decode(x >> 16)))

  def cmd_init(self, ui, args):
    """initialize the flexspi controller"""
    self.lut_unlock()
    for i in range(64):
      self.hw.registers['LUT%d' % i].wr(0)
    self.lut_lock()

    # 0 Fast read Quad IO DTR Mode Operation in SPI Mode (normal read)
    self.lut_set(0, 0, op_encode(OPCODE_CMD_SDR, PAD_X1, 0xED))
    self.lut_set(0, 1, op_encode(OPCODE_RADDR_DDR, PAD_X4, 0x18))
    self.lut_set(0, 2, op_encode(OPCODE_DUMMY_DDR, PAD_X4, 0x0C))
    self.lut_set(0, 3, op_encode(OPCODE_READ_DDR, PAD_X4, 0x08))
    # 1 Read Status
    self.lut_set(1, 0, op_encode(OPCODE_CMD_SDR, PAD_X1, 0x05))
    self.lut_set(1, 1, op_encode(OPCODE_READ_SDR, PAD_X1, 0x01))
    # 3
    self.lut_set(3, 0, op_encode(OPCODE_CMD_SDR, PAD_X1, 0x06))
    # 5 Erase Sector
    self.lut_set(5, 0, op_encode(OPCODE_CMD_SDR, PAD_X1, 0xD7))
    self.lut_set(5, 1, op_encode(OPCODE_RADDR_SDR, PAD_X1, 0x18))
    # 9 Page Program
    self.lut_set(9, 0, op_encode(OPCODE_CMD_SDR, PAD_X1, 0x02))
    self.lut_set(9, 1, op_encode(OPCODE_RADDR_SDR, PAD_X1, 0x18))
    self.lut_set(9, 2, op_encode(OPCODE_WRITE_SDR, PAD_X1, 0x8))
    # 11 Chip Erase
    self.lut_set(11, 0, op_encode(OPCODE_CMD_SDR, PAD_X1, 0xC7))


#-----------------------------------------------------------------------------




