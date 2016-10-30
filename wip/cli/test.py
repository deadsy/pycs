#!/usr/bin/python
#-----------------------------------------------------------------------------

import sys
import cli

#-----------------------------------------------------------------------------

def cmd3_func(ui, args):
  """cmd3 help"""
  ui.put('%s\n' % str(args))

def cmd11_func(ui, args):
  """cmd11 help"""
  ui.put('%s\n' % str(args))

def cmd12_func(ui, args):
  """cmd12 help"""
  ui.put('%s\n' % str(args))

def cmd13_func(ui, args):
  """cmd13 help"""
  ui.put('%s\n' % str(args))

def cmd21_func(ui, args):
  """cmd21 help"""
  ui.put('%s\n' % str(args))

def cmd22_func(ui, args):
  """cmd22 help"""
  ui.put('%s\n' % str(args))

cmd2_menu = (
  ('cmd2.1', cmd21_func),
  ('cmd2.2', cmd22_func),
)

cmd1_menu = (
  ('cmd1.1', cmd11_func),
  ('cmd1.2', cmd12_func),
  ('cmd1.3', cmd13_func),
)

menu_root = (
  ('cmd1', cmd1_menu, 'cmd1 functions'),
  ('cmd2', cmd2_menu, 'cmd2 functions'),
  ('cmd3', cmd3_func),
)

#-----------------------------------------------------------------------------

class user_interface(object):

  def __init__(self):
    self.cli = cli.cli(self, 'history.txt')
    self.cli.set_root(menu_root)
    self.cli.set_prompt('hello> ')

  def exit(self):
    self.cli.exit()

  def put(self, s):
    sys.stdout.write(s)

  def run(self):
    self.cli.run()

  def cmd_help(self, ui, args):
    """general help"""
    self.cli.general_help()

#-----------------------------------------------------------------------------

def main():
  ui = user_interface()
  ui.run()
  sys.exit(0)

main()

#-----------------------------------------------------------------------------
