#------------------------------------------------------------------------------
"""

USB Device

A generic class for reading/writing USB devices.

"""
#------------------------------------------------------------------------------

import usb.core
from array import array as Array
from usbtools.usbtools import UsbTools

#------------------------------------------------------------------------------

def find(vps, sn = None):
  """lookup a usb device based on vid, pid and serial number"""
  devices = UsbTools.find_all(vps)
  # do we have any devices?
  if len(devices) == 0:
    return None, 'no device found'
  if sn is not None:
    # filter using the serial number
    devices_sn = [d for d in devices if d[2] == sn]
    if len(devices_sn) == 0:
      # we have devices, but none with this serial number
      s = []
      s.append('no device with this serial number')
      s.append('devices found:')
      for d in devices:
        s.append('%04x:%04x sn %r' % (d[0], d[1], d[2]))
      return None, '\n'.join(s)
    else:
      devices = devices_sn
  # no devices
  if len(devices) == 0:
    return None, 'no device found'
  # multiple devices
  if len(devices) > 1:
    s = []
    s.append('multiple devices found:')
    for d in devices:
      s.append('%04x:%04x sn %r' % (d[0], d[1], d[2]))
    return None, '\n'.join(s)
  # 1 device
  return devices[0], None

#------------------------------------------------------------------------------

class usbdev_error(IOError):
  """communication error with the USB device"""

class usbdev(object):
  """generic USB device driver with read/write interface"""

  def __init__(self):
    self.usb_dev = None
    self.usb_rd_timeout = 5000
    self.usb_wr_timeout = 5000
    self.rdbuf = Array('B')
    self.rdofs = 0
    self.rdbuf_chunksize = 4 << 10
    self.wrbuf_chunksize = 4 << 10
    self.itf = None
    self.index = None
    self.ep_in = None
    self.ep_out = None
    self._wrap_api()

  # public functions

  def open(self, vendor, product, interface=1, index=0, serial=None, description=None):
    """open a new interface to the specified device"""
    self.usb_dev = UsbTools.get_device(vendor, product, index, serial, description)
    config = self.usb_dev.get_active_configuration()
    # check for a valid interface
    if interface > config.bNumInterfaces:
      raise usbdev_error('invalid interface: %d' % interface)
    self._set_interface(config, interface)

  def close(self):
    """close the interface"""
    UsbTools.release_device(self.usb_dev)

  def write_data(self, data):
    """write a data buffer to the device"""
    ofs = 0
    size = len(data)
    try:
      while ofs < size:
        # how many bytes should we write?
        wr_size = self.wrbuf_chunksize
        if wr_size > size - ofs:
          # reduce the write size
          wr_size = size - ofs
        # write the bytes
        n = self._write(data[ofs : ofs + wr_size])
        if n <= 0:
          raise usbdev_error("USB bulk write error")
        ofs += n
      # return the number of bytes written
      return ofs
    except usb.core.USBError, e:
      raise usbdev_error(str(e))

  def read_data(self, size, attempts = 1):
    """read size bytes of data from the device"""
    data = Array('B')
    # do we have all of the data in the read buffer?
    if size <= len(self.rdbuf) - self.rdofs:
      data = self.rdbuf[self.rdofs : self.rdofs + size]
      self.rdofs += size
      return data
    # do we have some of the data in the read buffer?
    if len(self.rdbuf) - self.rdofs > 0:
      data = self.rdbuf[self.rdofs:]
      # do a usb read to get the rest...
    # read from the usb device
    try:
      bytes_to_rd = size - len(data)
      while bytes_to_rd > 0:
        # read from the usb device
        while True:
          self.rdbuf = self._read()
          self.rdofs = 0
          if len(self.rdbuf) > 0:
            break
          else:
            # no data received
            attempts -= 1
            if attempts > 0:
              # try again
              continue
              # return what we have
              return data
        # copy the read buffer into the returned data
        n = len(self.rdbuf)
        if n >= bytes_to_rd:
          # copy a partial read buffer
          data += self.rdbuf[:bytes_to_rd]
          self.rdofs = bytes_to_rd
          return data
        else:
          # copy all of the read buffer
          data += self.rdbuf
          bytes_to_rd -= n
          # read more data...
    except usb.core.USBError, e:
      raise usbdev_error(str(e))
    # never reached
    raise usbdev_error("internal error")

  # private functions

  def _wrap_api(self):
    """set _read/_write to match the USB api version"""
    import inspect
    args, varargs, varkw, defaults = inspect.getargspec(usb.core.Device.read)
    if (len(args) > 2) and (args[3] == 'interface'):
      usb_api = 1  # Require "interface" parameter
    else :
      usb_api = 2
    for m in ('write', 'read'):
      setattr(self, '_%s' % m, getattr(self, '_%s_v%d' % (m, usb_api)))

  def _set_interface(self, config, ifnum):
    """select the interface to use"""
    if ifnum == 0:
      ifnum = 1
    if ifnum-1 not in xrange(config.bNumInterfaces):
      raise ValueError("invalid interface for this device")
    self.index = ifnum
    self.interface = config[(ifnum-1, 0)]
    endpoints = sorted([ep.bEndpointAddress for ep in self.interface])
    self.ep_out, self.ep_in = endpoints[:2]

  def _write_v1(self, data):
    """Write using the deprecated API"""
    return self.usb_dev.write(self.ep_out, data, self.interface, self.usb_wr_timeout)

  def _read_v1(self):
    """Read using the deprecated API"""
    return self.usb_dev.read(self.ep_in, self.rdbuf_chunksize, self.interface, self.usb_rd_timeout)

  def _write_v2(self, data):
    """Write using the API introduced with pyusb 1.0.0b2"""
    return self.usb_dev.write(self.ep_out, data, self.usb_wr_timeout)

  def _read_v2(self):
    """Read using the API introduced with pyusb 1.0.0b2"""
    return self.usb_dev.read(self.ep_in, self.rdbuf_chunksize, self.usb_rd_timeout)

#------------------------------------------------------------------------------

