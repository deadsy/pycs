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

_not_initialised = 'rtt is not initialised'

_CTRL_D = chr(4) # exit rtt monitoring

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
    # get the flags
    self.flags = self.cpu.rd(self.adr + 20, 32)
    # record the other addresses for future reference
    self.wr_ofs_adr = self.adr + 12
    self.rd_ofs_adr = self.adr + 16

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

    ui.put('wr ofs 0x%x\n' % wr_ofs)
    ui.put('rd ofs 0x%x\n' % rd_ofs)

    if wr_ofs != rd_ofs:
      buf = iobuf.data_buffer(8)
      if rd_ofs < wr_ofs:
        # read to write offset
        self.cpu.rdmem(self.buf_adr + rd_ofs, wr_ofs - rd_ofs, buf)
      else:
        # read to end of buffer
        self.cpu.rdmem(self.buf_adr + rd_ofs, self.buf_size - rd_ofs, buf)
        # read to write offset
        self.cpu.rdmem(self.buf_adr, wr_ofs, buf)
      self.cpu.wr(self.rd_ofs_adr, wr_ofs, 32)
      ui.put('%d bytes read\n' % len(buf))
      ui.put('%s\n' % buf.ascii_str())
    else:
      ui.put('0 bytes read\n')

  def read(self):
    """read the buffer"""
    wr_ofs = self.cpu.rd(self.wr_ofs_adr, 32)
    rd_ofs = self.cpu.rd(self.rd_ofs_adr, 32)
    # do we have data?
    if wr_ofs != rd_ofs:
      # we have data - read it
      # TODO: possible performance improvement with 32 bit reads
      buf = iobuf.data_buffer(8)
      if rd_ofs < wr_ofs:
        # non-wrapped buffer: read to write offset
        self.cpu.rdmem(self.buf_adr + rd_ofs, wr_ofs - rd_ofs, buf)
      else:
        # wrapped buffer: read to end of buffer
        self.cpu.rdmem(self.buf_adr + rd_ofs, self.buf_size - rd_ofs, buf)
        # read to write offset
        self.cpu.rdmem(self.buf_adr, wr_ofs, buf)
      # we are caught up: read offset == write offset
      self.cpu.wr(self.rd_ofs_adr, wr_ofs, 32)
      return buf
    else:
      # no data
      return None

  def text_dump(self, ui, delimiter = '\r'):
    """assume the buffer contains null delimited text"""
    buf = self.read()
    if buf is None:
      return
    ui.put(buf.to_str())
    #s = buf.to_str()
    #print s

    #s = s.split('\r')
    #ui.put('%s\n' % str(s))

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
      ('mon', self.cmd_mon),
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

  def cmd_mon(self, ui, args):
    """monitor and display the rtt buffers"""
    if self.adr is None:
      ui.put('%s\n' % _not_initialised)
      return
    ui.put('Monitoring target to host RTT buffers\nCtrl-D to exit\n')
    while True:
      c = ui.poll()
      if c == _CTRL_D:
        break
      else:
        # read the target to host buffers
        for b in self.t2h:
          b.text_dump(ui)

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
    if self.adr is None:
      ui.put('%s\n' % _not_initialised)
      return
    # print the rtt info
    cols = []
    cols.append(['rtt address', ': 0x%08x' % self.adr])
    if len(self.t2h) > 0:
      cols.extend([['target to host', ': %s' % b] for b in self.t2h])
    if len(self.h2t) > 0:
      cols.extend([['host to target', ': %s' % b] for b in self.h2t])
    ui.put('%s\n' % util.display_cols(cols))

#-----------------------------------------------------------------------------
