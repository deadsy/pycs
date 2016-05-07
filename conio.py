#-----------------------------------------------------------------------------
"""
Console IO

Provides non-blocking, non-echoing access to the console interface.
"""
#-----------------------------------------------------------------------------

import os
import select
import termios
import sys

#-----------------------------------------------------------------------------
# when otherwise idle, allow other things to run

_poll_timeout = 0.5  # secs

#-----------------------------------------------------------------------------

CHAR_NULL = 0x00
CHAR_BELL = 0x07
CHAR_TAB = 0x09
CHAR_CR = 0x0a
CHAR_DOWN = 0x10
CHAR_UP = 0x11
CHAR_LEFT = 0x12
CHAR_RIGHT = 0x13
CHAR_END = 0x14
CHAR_HOME = 0x15
CHAR_ESC = 0x1b
CHAR_SPACE = 0x20
CHAR_QM = 0x3f
CHAR_BS = 0x7f
CHAR_DEL = 0x7e

#-----------------------------------------------------------------------------


class console:

  def __init__(self):
    """set the console to non-blocking, non-echoing"""
    self.fd = os.open(os.ctermid(), os.O_RDWR)
    self.saved = termios.tcgetattr(self.fd)
    new = termios.tcgetattr(self.fd)
    new[3] &= ~termios.ICANON
    new[3] &= ~termios.ECHO
    termios.tcsetattr(self.fd, termios.TCSANOW, new)

  def close(self):
    """restore original console settings"""
    termios.tcsetattr(self.fd, termios.TCSANOW, self.saved)
    os.close(self.fd)

  def get(self):
    """get console input - return ascii code"""
    # block until we can read or we have a timeout
    (rd, wr, er) = select.select((self.fd,), (), (), _poll_timeout)
    if len(rd) == 0:
      # timeout - allow other routines to run
      return CHAR_NULL

    # make copy+paste work
    x = os.read(self.fd, 1)
    # escape sequence ?
    if ord(x) == 0x1b:
      x = os.read(self.fd, 1)
      # control characters ?
      if ord(x) == 0x5b:
        x = os.read(self.fd, 1)
        # handle known items
        if ord(x) == 0x41:
          return CHAR_UP
        elif ord(x) == 0x42:
          return CHAR_DOWN
        elif ord(x) == 0x43:
          return CHAR_RIGHT
        elif ord(x) == 0x44:
          return CHAR_LEFT
        elif ord(x) == 0x46:
          return CHAR_END
        elif ord(x) == 0x48:
          return CHAR_HOME

    # return single char
    return ord(x)

  def put(self, s):
    """output a string to console"""
    os.write(self.fd, s)

#-----------------------------------------------------------------------------
