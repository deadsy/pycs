#------------------------------------------------------------------------------
"""

ST-Link Driver

Sources:
https://github.com/texane/stlink

"""
#------------------------------------------------------------------------------

import struct
from array import array as Array
from usbtools.usbtools import UsbTools
import usbdev

#------------------------------------------------------------------------------
# supported devices

stlink_devices = (
  (0x0483, 0x3744, 1), # Version 1
  (0x0483, 0x3748, 1), # Version 2
  (0x0483, 0x374B, 1), # Version 2.1
)

def itf_lookup(vid, pid):
  """return the interface to use for a given device"""
  for (v, p, i) in stlink_devices:
    if (v == vid) and (p == pid):
      return i
  return None

def find(vps = None, sn = None):
  """find an stlink device based on vid, pid and serial number"""
  if vps is None:
    # look for any jlink device
    vps = [(vid, pid) for (vid, pid, itf) in stlink_devices]
  return usbdev.find(vps, sn)

#------------------------------------------------------------------------------

GET_VERSION = 0xF1
DEBUG_COMMAND = 0xF2
DFU_COMMAND = 0xF3
SWIM_COMMAND = 0xF4
GET_CURRENT_MODE = 0xF5
GET_TARGET_VOLTAGE = 0xF7

#------------------------------------------------------------------------------

class stlink(object):
  """ST-Link Device Driver"""

  def __init__(self, dev):
    self.vid = dev[0]
    self.pid = dev[1]
    self.sn = dev[2]
    itf = itf_lookup(self.vid, self.pid)
    self.usb = usbdev.usbdev()
    self.usb.open(self.vid, self.pid, interface = itf, serial = self.sn)

  def get_version(self):
    """return the ST-Link version"""
    self.usb.write_data(Array('B', [GET_VERSION,]))
    x = self.usb.read_data(6)
    ver = {}
    ver['stlink_v'] = (x[0] & 0xf0) >> 4
    ver['jtag_v'] = ((x[0] & 0x0f) << 2) | ((x[1] & 0xc0) >> 6)
    ver['swim_v'] = x[1] & 0x3f
    ver['st_vid'] = (x[3] << 8) | x[2]
    ver['stlink_pid'] = (x[5] << 8) | x[4]
    return ver

  def __str__(self):
    """return a string for basic device description"""
    return 'ST-Link usb %04x:%04x serial %r' % (self.vid, self.pid, self.sn)

#------------------------------------------------------------------------------
