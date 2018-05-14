#!/usr/bin/python

import unittest
import bits

str0 = '11011110101011011011111011101111'

class TestBits(unittest.TestCase):

  def test1(self):
    x = bits.null()
    self.assertEqual(str(x), '(0) ')

  def test2(self):
    x = bits.ones(3)
    self.assertEqual(str(x), '(3) 111')

  def test3(self):
    x = bits.zeroes(7)
    self.assertEqual(str(x), '(7) 0000000')

  def test4(self):
    x = bits.zeroes(7).tail1(4)
    self.assertEqual(str(x), '(11) 11110000000')

  def test5(self):
    x = bits.ones(7).tail0(4)
    self.assertEqual(str(x), '(11) 00001111111')

  def test6(self):
    x = bits.from_tuple((1, 1, 1, 0, 1))
    self.assertEqual(str(x), '(5) 11101')

  def test7(self):
    x = bits.from_tuple('011111')
    self.assertEqual(str(x), '(6) 011111')

  def test8(self):
    x = bits.from_random(10)
    y = bits.from_random(10)
    z = x.copy().head(y)
    self.assertEqual(x.bit_str() + y.bit_str(), z.bit_str())

  def test9(self):
    x = bits.from_random(10)
    y = bits.from_random(10)
    z = x.copy().tail(y)
    self.assertEqual(y.bit_str() + x.bit_str(), z.bit_str())

  def test10(self):
    x = bits.from_tuple('11111111')
    y = x.get_bytes()
    self.assertEqual(len(y), 1)
    self.assertEqual(y[0], 255)

  def test11(self):
    x = bits.from_tuple('11011110101011011011111011101111')
    y = x.get_bytes()
    self.assertEqual(len(y), 4)
    self.assertEqual(y[0], 0xef)
    self.assertEqual(y[1], 0xbe)
    self.assertEqual(y[2], 0xad)
    self.assertEqual(y[3], 0xde)

  def test12(self):
    x = bits.bits().set_bytes((0xff,), 7)
    self.assertEqual(str(x), '(7) 1111111')
    x = bits.bits().set_bytes((0x1,), 7)
    self.assertEqual(str(x), '(7) 0000001')
    x = bits.bits().set_bytes((64,), 7)
    self.assertEqual(str(x), '(7) 1000000')

  def test13(self):
    x = bits.from_tuple(str0)
    y = bits.bits().set_bytes(x.get_bytes(), len(str0))
    self.assertEqual(y.bit_str(), str0)

if __name__ == '__main__':
  unittest.main()
