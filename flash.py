#-----------------------------------------------------------------------------
"""
Flash Commands

This code is the generic front end to flash programming operations.
The vendor specific flash drivers are within the vendor directories.
Those drivers expose a common API used by this code.
"""
#-----------------------------------------------------------------------------

_help_erase = (
  ('<adr> <len>', 'flash address (hex) rounded down to a flash page boundary'),
  ('', 'flash length (hex) rounded up to n flash pages'),
  ('<name>', 'erase named flash region'),
)

#-----------------------------------------------------------------------------

class flash(object):

  def __init__(self, driver):
    self.driver = driver
    self.menu = (
      ('ep', self.cmd_ep),
      ('epv', self.cmd_epv),
      ('erase', self.cmd_erase, _help_erase),
      ('info', self.cmd_info),
      ('program', self.cmd_program),
      ('verify', self.cmd_verify),
    )

  def cmd_ep(self, ui, args):
    """erase and program flash"""
    pass

  def cmd_epv(self, ui, args):
    """erase, program and verify flash"""
    pass

  def cmd_erase(self, ui, args):
    """erase flash"""




    self.driver.erase(0, 1)

  def cmd_info(self, ui,args):
    """display flash information"""
    ui.put('%s\n' % self.driver)

  def cmd_program(self, ui, args):
    """program flash"""
    pass

  def cmd_verify(self, ui, args):
    """verify flash"""
    pass



#-----------------------------------------------------------------------------


