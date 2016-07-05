#-----------------------------------------------------------------------------
"""
GPIO Commands

This code is the generic front end for GPIO operations.
The vendor specific flash drivers are within the vendor directories.
Those drivers expose a common API used by this code.
"""
#-----------------------------------------------------------------------------



#-----------------------------------------------------------------------------

_help_gpio = (
    ('[name]', 'gpio name (see status)'),
)

#-----------------------------------------------------------------------------

class gpio(object):

  def __init__(self, driver):
    self.driver = driver
    self.menu = (
      ('clr', self.cmd_clr, _help_gpio),
      ('info', self.cmd_info),
      ('set', self.cmd_set, _help_gpio),
    )

  def cmd_clr(self, ui, args):
    """clear gpio (0)"""
    pass

  def cmd_set(self, ui, args):
    """set gpio (1)"""
    pass

  def cmd_info(self, ui, args):
    """display gpio information"""
    ui.put('%s\n' % self.driver)

#-----------------------------------------------------------------------------
