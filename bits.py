# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
"""
Bit Buffer Operations
"""
#-----------------------------------------------------------------------------

import random
import array

#-----------------------------------------------------------------------------

class bits:

    def __init__(self, n = 0, val = 0):
        val &= ((1 << n) - 1)
        self.n = n
        self.val = val

    def clear(self):
        """remove any contents"""
        self.n = 0
        self.val = 0

    def ones(self, n):
        """set n bits to 1"""
        self.n = n
        self.val = (1 << n) - 1

    def zeroes(self, n):
        """set n bits to 0"""
        self.n = n
        self.val = 0

    def random(self, n):
        """set n bits to random values"""
        self.append_str(''.join([('0', '1')[random.randint(0, 1)] for i in xrange(n)]))

    def append(self, bits):
        """append a bit buffer to the bit buffer"""
        self.append_val(bits.n, bits.val)

    def append_val(self, n, val):
        """append n bits from val to the bit buffer"""
        val &= ((1 << n) - 1)
        self.val <<= n
        self.val |= val
        self.n += n

    def append_ones(self, n):
        """append n 1 bits to the bit buffer"""
        val = ((1 << n) - 1)
        self.val <<= n
        self.val |= val
        self.n += n

    def append_zeroes(self, n):
        """append n 0 bits to the bit buffer"""
        self.val <<= n
        self.n += n

    def append_str(self, s):
        """append a bit string to the bit buffer"""
        self.append_val(len(s), int(s, 2))

    def drop_lsb(self, n):
        """drop the least significant n bits"""
        if n < self.n:
            self.val >>= n
            self.n -= n
        else:
            self.n = 0
            self.val = 0

    def drop_msb(self, n):
        """drop the most significant n bits"""
        if n < self.n:
            self.n -= n
            self.val &= ((1 << self.n) - 1)
        else:
            self.n = 0
            self.val = 0

    def shr(self, bit_in = 0):
        """shift right"""
        bit_out = self.val & 1
        self.val >>= 1
        self.val |= (bit_in << (self.n - 1))
        return bit_out

    def reverse(self):
        """reverse the bits"""
        x = 0
        for i in xrange(self.n):
          if (self.val >> i) & 1:
            x |= 1 << (self.n - 1 - i)
        self.val = x

    def get(self):
        """return a byte array of the bits"""
        a = array.array('B')
        n = self.n
        val = self.val
        while n > 0:
            if n > 8:
                a.append(val & 255)
                val >>= 8
                n -= 8
            else:
                val &= (1 << n) - 1
                a.append(val)
                break
        return a

    def get_reverse(self):
        """reverse the bits before returning the byte array"""
        self.reverse()
        return self.get()

    def set(self, n, a):
        """set the bits from a byte array"""
        self.val = 0
        self.n = n
        for i in range(len(a) - 1, -1, -1):
            self.val <<= 8
            self.val |= a[i]

    def from_str(self, s):
        """set the bits from a 0/1 string"""
        self.n = len(s)
        self.val = 0
        for c in s:
          self.val <<= 1
          if c == '1':
            self.val += 1

    def scan(self, format):
        """using the format tuple, scan the buffer and return a tuple of values"""
        l = []
        val = self.val
        format_list = list(format)
        format_list.reverse()
        for n in format_list:
            mask = (1 << n) - 1
            l.append(val & mask)
            val >>= n
        l.reverse()
        return tuple(l)

    def __and__(self, x):
        return bits(min(self.n, x.n), self.val & x.val)

    def __eq__(self, x):
        return (self.n == x.n) and (self.val == x.val)

    def __ne__(self, x):
        return not ((self.n == x.n) and (self.val == x.val))

    def __str__(self):
        return '(%d) %x' % (self.n, self.val)

    def __len__(self):
        return self.n

    def bit_str(self):
        """return a bit string for the buffer"""
        n = self.n
        val = self.val
        l = []
        while n > 0:
            l.append(('0', '1')[val & 1])
            val >>= 1
            n -= 1
        l.reverse()
        return ''.join(l)

#-----------------------------------------------------------------------------
