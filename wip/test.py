#!/usr/bin/python

class register(object):

  def __init__(self, name):
    self.name = name
    
  def rd(self, idx = 0):  



class peripheral(object):

  def __init__(self, name):
    self.name = name
    self.registers = {
      'R0' : register('R0'),
      'R1' : register('R1'),
      'R2' : register('R2'),
      }

  def __getattr__(self, name):
    print('peripheral getattr(%s)' % name)
    return self.registers.get(name, None)

class device(object):

  def __init__(self, name):
    self.name = name
    self.peripherals = {
      'P0' : peripheral('P0'),
      'P1' : peripheral('P1'),
      'P2' : peripheral('P2'),
    }

  def __getattr__(self, name):
    print('device getattr(%s)' % name)
    return self.peripherals.get(name, None)

d = device('d0')

print d.P0.R0.name
print d.P1.R1.name
