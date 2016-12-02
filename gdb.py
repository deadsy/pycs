#-----------------------------------------------------------------------------
"""
GDB Server
"""
#-----------------------------------------------------------------------------

import socket

#-----------------------------------------------------------------------------
"""

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 32  # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print 'a'

s.bind((TCP_IP, TCP_PORT))
print 'b'
s.listen(1)
print 'c'

conn, addr = s.accept()
print 'Connection address:', addr

while True:
  data = conn.recv(BUFFER_SIZE)
  if not data:
    break
  print "received data:", data

  #conn.send(data)  # echo

conn.close()

"""

testbuf = (
  "+"
  "$qSupported:multiprocess+;swbreak+;hwbreak+;qRelocInsn+#c9"
  "$qSupported:multiprocess+;swbreak+;hwbreak+;qRelocInsn+#c9"
  "$qSupported:multiprocess+;swbreak+;hwbreak+;qRelocInsn+#c9"
  "$qSupported:multiprocess+;swbreak+;hwbreak+;qRelocInsn+#c9"
  "---+"
  "$Hg0#df"
  "$Hg0#df"
  "$Hg0#df"
  "$Hg0#df"
  "---+"
  "$qTStatus#49"
  "$qTStatus#49"
  "$qTStatus#49"
  "$qTStatus#49"
  "---+"
)

#-----------------------------------------------------------------------------

class gdb(object):

  def __init__(self, cpu):
    self.cpu = cpu
    self.port = 3333                  # gdb listening port
    self.rx_state = self.wait4_start  # receive packet state
    self.rx_cs = []                   # receive packet checksum
    self.rx_data = []                 # receive packet data

  def rx_ack(self):
    print('ack')

  def rx_nak(self):
    print('nak')

  def rx_cmd(self, cmd):
    print('%s' % cmd)

  def csum_good(self, data, cs):
    csum = 0
    for c in data:
      csum += ord(c)
    return int(cs, 16) == csum % 256

  def wait4_start(self, c):
    """wait for the packet start delimiter"""
    if c == '+':
      self.rx_ack()
    elif c == '-':
      self.rx_nak()
    elif c == '$':
      # get the packet data
      self.rx_data = []
      self.rx_state = self.wait4_end
    else:
      # keep on waiting...
      pass

  def wait4_end(self, c):
    """wait for the packet end delimiter"""
    if c == '#':
      # get the checksum
      self.rx_cs = []
      self.rx_state = self.wait4_checksum
    else:
      # accumulate the packet data
      self.rx_data.append(c)

  def wait4_checksum(self, c):
    """wait for the checksum characters"""
    # accumulate the checksum character
    self.rx_cs.append(c)
    if len(self.rx_cs) == 2:
      # we have the checksum
      cs = ''.join(self.rx_cs)
      data = ''.join(self.rx_data)
      if self.csum_good(data, cs):
        self.rx_cmd(data)
      else:
        # TODO: bad checksum - send a nak
        pass
      self.rx_state = self.wait4_start

  def rx(self, buf):
    """receive a buffer of characters"""
    for c in buf:
      self.rx_state(c)

  def run(self, ui, args):
    """run the gdb server"""
    self.rx(testbuf)

#-----------------------------------------------------------------------------
