#------------------------------------------------------------------------------
"""

USB Device

A generic class for dealing with reading/writing to USB devices.

"""
#------------------------------------------------------------------------------

import usb.core
import array

from usbtools.usbtools import UsbTools

#------------------------------------------------------------------------------

class usbdev_error(IOError):
  """communication error with the USB device"""

class usbdev(object):
  """generic USB device driver with read/write interface"""

  def __init__(self):
    self.usb_dev = None                   # usb device handle
    self.usb_read_timeout = 5000          # read timeout in ms
    self.usb_write_timeout = 5000         # write timeout in ms
    self.readbuffer = array.array('B')    # local read buffer
    self.readoffset = 0                   # current offset into local read buffer
    self.readbuffer_chunksize = 4 << 10   # 4KiB
    self.writebuffer_chunksize = 4 << 10  # 4KiB
    self.interface = None                 # selected interface within usb device
    self.index = None
    self.in_ep = None                     # device endpoint for writing
    self.out_ep = None                    # device endpoint for reading
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
    self.max_packet_size = self._get_max_packet_size()

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
        wr_size = self.writebuffer_chunksize
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
      raise usbdev_error('usbdev_error: %s' % str(e))

  def read_data(self, size, attempt=1):
    """read size bytes of data from the device"""

    # check max_packet_size
    if not self.max_packet_size:
      raise usbdev_error("max_packet_size is not set")

    # initial condition to enter the usb_read loop
    packet_size = self.max_packet_size
    length = 1
    data = array.array('B')

    # do we have size bytes in the readbuffer?
    if size <= len(self.readbuffer) - self.readoffset:
      data = self.readbuffer[self.readoffset : self.readoffset + size]
      self.readoffset += size
      return data

    # do we have some data in the readbuffer?
    if len(self.readbuffer) - self.readoffset != 0:
      data = self.readbuffer[self.readoffset:]
      # end of readbuffer reached
      self.readoffset = len(self.readbuffer)
      # do a usb read to get the rest...

    # read from USB, filling in the local cache as it is empty
    try:
      while (len(data) < size) and (length > 0):




        while True:
          tempbuf = self._read()
          attempt -= 1
          length = len(tempbuf)
          if length > 0:
            # skip the status bytes
            chunks = (length + packet_size - 1) // packet_size
            count = packet_size
            self.readbuffer = array.array('B')
            self.readoffset = 0
            srcoff = 0
            for i in xrange(chunks):
              self.readbuffer += tempbuf[srcoff : srcoff + count]
              srcoff += packet_size
            length = len(self.readbuffer)
            break
          else:
            # no data received, may be late, try again
            if attempt > 0:
              continue
            # no actual data
            self.readbuffer = array.array('B')
            self.readoffset = 0
            # no more data to read?
            return data



        if length > 0:
          # data still fits in buf?
          if (len(data) + length) <= size:
            data += self.readbuffer[self.readoffset : self.readoffset + length]
            self.readoffset += length
            # did we read exactly the right amount of bytes?
            if len(data) == size:
              return data
          else:
            # partial copy, not enough bytes in the local cache to fulfill the request
            part_size = min(size-len(data), len(self.readbuffer)-self.readoffset)
            if part_size < 0:
              raise AssertionError("internal error")
            data += self.readbuffer[self.readoffset:self.readoffset+part_size]
            self.readoffset += part_size
            return data


    except usb.core.USBError, e:
      raise usbdev_error('usbdev_error: %s' % str(e))
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
      raise ValueError("No such interface for this device")
    self.index = ifnum
    self.interface = config[(ifnum-1, 0)]
    endpoints = sorted([ep.bEndpointAddress for ep in self.interface])
    self.in_ep, self.out_ep = endpoints[:2]

  def _write_v1(self, data):
    """Write using the deprecated API"""
    return self.usb_dev.write(self.in_ep, data, self.interface, self.usb_write_timeout)

  def _read_v1(self):
    """Read using the deprecated API"""
    return self.usb_dev.read(self.out_ep, self.readbuffer_chunksize, self.interface, self.usb_read_timeout)

  def _write_v2(self, data):
    """Write using the API introduced with pyusb 1.0.0b2"""
    return self.usb_dev.write(self.in_ep, data, self.usb_write_timeout)

  def _read_v2(self):
    """Read using the API introduced with pyusb 1.0.0b2"""
    return self.usb_dev.read(self.out_ep, self.readbuffer_chunksize, self.usb_read_timeout)

  def _get_max_packet_size(self):
    """get the maximum length of a data packet"""
    if not self.usb_dev:
      raise AssertionError("device is not known")
    if not self.interface:
      raise AssertionError("interface is not known")
    return self.interface[0].wMaxPacketSize

#------------------------------------------------------------------------------

