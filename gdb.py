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
#-----------------------------------------------------------------------------

class gdb(object):

  def __init__(self, port):
    self.port = port                  # gdb listening port
    self.rx_state = self.wait4_start  # receive packet state
    self.rx_cs = []                   # receive packet checksum
    self.rx_data = []                 # receive packet data

  def wait4_start(self, c):
    """wait for the packet start delimiter"""
    if c == '$':
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
      self.rx_state == self.wait4_checksum
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
      # TODO process the checksum
      self.ui.put('data: %s cs %s' % (data, cs))
      self.rx_state == self.wait4_start

  def wait4_ack(self, c):
    """wait for an acknowledgement"""
    if c == '+':
      # ack TODO clear the packet
      pass
    elif c == '-':
      # nack TODO retransmit
      pass
    else:
      # what is this?
      pass

  def rx(self, buf):
    """receive a buffer of characters"""
    for c in buf:
      self.rx_state(c)



#-----------------------------------------------------------------------------
