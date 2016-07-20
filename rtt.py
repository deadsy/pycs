#-----------------------------------------------------------------------------
"""

Segger RTT Client

The Segger RTT code implements circular buffers on the target.
This code finds the buffers in RAM and then reads them as the target code runs.

"""
#-----------------------------------------------------------------------------

import util
import iobuf

#-----------------------------------------------------------------------------

sizeof_SEGGER_RTT_CB_header = 24
sizeof_SEGGER_RTT_RING_BUFFER = 24

#-----------------------------------------------------------------------------

class rtt_buf(object):
  """rtt buffer object"""

  def __init__(self, cpu, adr):
    self.cpu = cpu
    self.adr = adr
    # get the name
    self.name = self.get_name(self.cpu.rd(self.adr, 32))
    # get the buffer address
    self.buf_adr = self.cpu.rd(self.adr + 4, 32)
    # get the buffer size
    self.buf_size = self.cpu.rd(self.adr + 8, 32)
    # record the other addresses for future reference
    self.wr_ofs_adr = self.adr + 12
    self.rd_ofs_adr = self.adr + 16
    self.flags_adr = self.adr + 20

  def get_name(self, adr):
    if adr == 0:
      return ''
    s = []
    while True:
      c = self.cpu.rd(adr, 8)
      if c == 0:
        break
      adr += 1
      s.append(chr(c))
    return ''.join(s)

  def poll(self, ui):
    """poll this buffer"""
    wr_ofs = self.cpu.rd(self.wr_ofs_adr, 32)
    rd_ofs = self.cpu.rd(self.rd_ofs_adr, 32)
    flags = self.cpu.rd(self.flags_adr, 32)

    ui.put('wr ofs %x\n' % wr_ofs)
    ui.put('rd ofs %x\n' % rd_ofs)
    ui.put('flags %x\n' % flags)

    if wr_ofs != rd_ofs:
      buf = iobuf.data_buffer(8)
      if rd_ofs < wr_ofs:
        # read to write offset
        self.cpu.rdmem8(self.buf_adr + rd_ofs, wr_ofs - rd_ofs, buf)
      else:
        # read to end of buffer
        self.cpu.rdmem8(self.buf_adr + rd_ofs, self.buf_size - rd_ofs, buf)
        # read to write offset
        self.cpu.rdmem8(self.buf_adr, wr_ofs, buf)
    self.cpu.wr(self.rd_ofs_adr, wr_ofs, 32)

    ui.put('%d bytes read\n' % len(buf))
    ui.put('%s\n' % buf.ascii_str())

  def __str__(self):
    return '%s %d bytes @ 0x%08x' % (self.name, self.buf_size, self.buf_adr)

#-----------------------------------------------------------------------------

class rtt(object):

  def __init__(self, cpu, mem):
    self.cpu = cpu
    # sanity check the rtt memory region
    assert mem.size >= 16, 'need at least 16 bytes for rtt signature matching'
    assert (mem.adr & 3 == 0) and (mem.size & 3 == 0), 'rtt ram must be 32 bit aligned'
    self.mem = mem
    self.adr = None
    self.menu = (
      ('init', self.cmd_init),
      ('info', self.cmd_info),
      ('poll', self.cmd_poll),
    )

  def look_for_sig(self, state, x):
    """look for the rtt buffer signature"""
    # signature = 'SEGGER RTT' + nulls, 16 bytes total
    # Note: the RTT init code on the target doesn't setup all 16 bytes.
    # We assume bss has been zeroed and the remaining bytes are null.
    # If bss hasn't been zeroed prior to calling main() then you need to fix that.
    sig = (0x47474553, 0x52205245, 0x5454, 0)
    if state is None:
      return (None, '1')[x == sig[0]]
    elif state == '1':
      return (None, '2')[x == sig[1]]
    elif state == '2':
      return (None, '3')[x == sig[2]]
    elif state == '3':
      return (None, 'match')[x == sig[3]]
    else:
      assert False, 'bad state'

  def find_rtt(self):
    """find the rtt buffers in ram"""
    adr = self.mem.adr
    state = None
    while adr < self.mem.end:
      state = self.look_for_sig(state, self.cpu.rd(adr, 32))
      adr += 4
      if state == 'match':
        break
    if state == 'match':
      # rewind to the start of the signature
      adr -= 16
    return (adr, state)

  def cmd_poll(self, ui, args):
    """process the target to host buffers"""
    for b in self.t2h:
      b.poll(ui)

  def cmd_init(self, ui, args):
    """initialise the rtt client"""
    # Call this code as often as you like.
    # It will re-init the rtt client and sync with changes made in RAM.
    (adr, state) = self.find_rtt()
    if state == 'match':
      ui.put('rtt signature found at 0x%08x\n' % adr)
      self.adr = adr
    else:
      ui.put('did not find rtt signature\n')
      self.adr = None
      return
    # starting address for rtt ring buffer structures
    adr = self.adr + sizeof_SEGGER_RTT_CB_header
    # target to host buffers
    n = self.cpu.rd(self.adr + 16, 32)
    self.t2h = []
    for i in range(n):
      self.t2h.append(rtt_buf(self.cpu, adr))
      adr += sizeof_SEGGER_RTT_RING_BUFFER
    # host to target buffers
    n = self.cpu.rd(self.adr + 20, 32)
    self.h2t = []
    for i in range(n):
      self.h2t.append(rtt_buf(self.cpu, adr))
      adr += sizeof_SEGGER_RTT_RING_BUFFER
    # remove any buffers with a size of 0
    self.t2h = [b for b in self.t2h if b.buf_size > 0]
    self.h2t = [b for b in self.h2t if b.buf_size > 0]


  def cmd_info(self, ui, args):
    """show rtt information"""
    if self.adr is not None:
      cols = []
      cols.append(['rtt address', ': 0x%08x' % self.adr])
      if len(self.t2h) > 0:
        cols.extend([['target to host', ': %s' % b] for b in self.t2h])
      if len(self.h2t) > 0:
        cols.extend([['host to target', ': %s' % b] for b in self.h2t])
      s = util.display_cols(cols)
    else:
      s = 'rtt is not initialised'
    ui.put('%s\n' % s)

#-----------------------------------------------------------------------------
