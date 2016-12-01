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
    self.port = port

#-----------------------------------------------------------------------------
