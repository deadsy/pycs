# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
"""
Input/Output Objects
Stateful objects used to produce/consume data from JTAG devices
"""
#-----------------------------------------------------------------------------

import struct
import util

#-----------------------------------------------------------------------------

_shifts8 = (0,)
_shifts32_be = (24, 16, 8, 0)
_shifts32_le = (0, 8, 16, 24)
_shifts64 = (56, 48, 40, 32, 24, 16, 8, 0)

_display32 = 'address   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F\n'
_display64 = 'address           0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F\n'

#-----------------------------------------------------------------------------

class to_display:
    """write data as a memory dump to the display"""

    def __init__(self, width, ui, adr, le = False):
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
        char_str = []
        for b in bytes:
            if (b > 126) or (b < 32):
                char_str.append('.')
            else:
                char_str.append(chr(b))
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

#-----------------------------------------------------------------------------

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
