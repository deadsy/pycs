#------------------------------------------------------------------------------
"""

Segger J-Link Driver

Tested with the J-Link Base

"""
#------------------------------------------------------------------------------

from usbtools import UsbTools

#------------------------------------------------------------------------------

# usb vendor:product IDs
_jlink_vps = (
    (0x1366, 0x0101), # J-Link Base
)

#------------------------------------------------------------------------------

class jlink:

  def __init__(self):
    self.usb_dev = None

  def open(self, vendor, product, interface, index=0, serial=None, description=None):
      """Open a new interface to the specified J-Link device"""
      self.usb_dev = UsbTools.get_device(vendor, product, index, serial, description)
      # detect invalid interface as early as possible
      config = self.usb_dev.get_active_configuration()

"""
  def __init__(self, sn):
    devices = usbtools.UsbTools.find_all(_jlink_vps)
    if sn is not None:
        # filter based on device serial number
        devices = [dev for dev in devices if dev[2] == sn]
    if len(devices) == 0:
        raise IOError("No such device")
    self.vid = devices[0][0]
    self.pid = devices[0][1]
    self.sn = devices[0][2]
"""

#------------------------------------------------------------------------------

class jtag:

  def __init__(self):
    pass

  def trst(self):
    """pulse the test reset line"""
    pass

  def srst(self):
    """pulse the system reset line"""
    pass

  def __str__(self):
      s = []
      s.append('Segger J-Link %04x:%04x serial %r' % (self.vid, self.pid, self.sn))
      return ', '.join(s)

#------------------------------------------------------------------------------

