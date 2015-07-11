#------------------------------------------------------------------------------
"""

Segger J-Link Driver

Tested with the J-Link Base

"""
#------------------------------------------------------------------------------

import os
import struct
import usb.core
import usb.util
from array import array as Array
from usbtools import UsbTools

#------------------------------------------------------------------------------
# usb vendor:product IDs

_jlink_vps = (
    (0x1366, 0x0101), # J-Link Base
)

#------------------------------------------------------------------------------

class JLinkError(IOError):
    """Communication error with the J-Link device"""

class JLink(object):
  """J-Link Device Driver"""

  # Document RM08001-R7 J-Link USB Protocol
  EMU_CMD_VERSION = 0x01            # Retrieves the firmware version.
  EMU_CMD_GET_SPEEDS = 0xC0         # Retrieves the base freq. and the min.divider of the emulator CPU.
  EMU_CMD_GET_MAX_MEM_BLOCK = 0xD4  # Retrieves the maximum memory block-size.
  EMU_CMD_GET_CAPS = 0xE8           # Retrieves capabilities of the emulator.
  EMU_CMD_GET_CAPS_EX = 0xED        # Retrieves capabilities (including extended ones) of the emulator.
  EMU_CMD_GET_HW_VERSION =  0xF0    # Retrieves the hardware version of the emulator.

  def __init__(self):
    self.usb_dev = None
    self.usb_read_timeout = 5000
    self.usb_write_timeout = 5000
    self.readbuffer = Array('B')
    self.readoffset = 0
    self.readbuffer_chunksize = 4 << 10 # 4KiB
    self.writebuffer_chunksize = 4 << 10 # 4KiB
    self.interface = None
    self.index = None
    self.in_ep = None
    self.out_ep = None
    self._wrap_api()

  # --- Public API -------------------------------------------------------

  def open(self, vendor, product, interface=1, index=0, serial=None, description=None):
    """Open a new interface to the specified J-Link device"""
    self.usb_dev = UsbTools.get_device(vendor, product, index, serial, description)
    config = self.usb_dev.get_active_configuration()
    # detect invalid interface as early as possible
    if interface > config.bNumInterfaces:
      raise JLinkError('No such J-Link port: %d' % interface)
    self._set_interface(config, interface)
    self.max_packet_size = self._get_max_packet_size()

  def close(self):
    """Close the J-Link interface"""
    UsbTools.release_device(self.usb_dev)

  def write_data(self, data):
    """Write data in chunks to the chip"""
    offset = 0
    size = len(data)
    try:
      while offset < size:
        write_size = self.writebuffer_chunksize
        if offset + write_size > size:
          write_size = size - offset
        length = self._write(data[offset:offset+write_size])
        if length <= 0:
          raise JLinkError("Usb bulk write error")
        offset += length
      return offset
    except usb.core.USBError, e:
      raise JLinkError('UsbError: %s' % str(e))

  def read_data_bytes(self, size, attempt=1):
    """Read data in chunks from the chip."""
    # Packet size sanity check
    if not self.max_packet_size:
      raise JLinkError("max_packet_size is bogus")
    packet_size = self.max_packet_size
    length = 1 # initial condition to enter the usb_read loop
    data = Array('B')
    # everything we want is still in the cache?
    if size <= len(self.readbuffer) - self.readoffset:
      data = self.readbuffer[self.readoffset : self.readoffset + size]
      self.readoffset += size
      return data
    # something still in the cache, but not enough to satisfy 'size'?
    if len(self.readbuffer) - self.readoffset != 0:
      data = self.readbuffer[self.readoffset:]
      # end of readbuffer reached
      self.readoffset = len(self.readbuffer)
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
            self.readbuffer = Array('B')
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
            self.readbuffer = Array('B')
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
            # partial copy, not enough bytes in the local cache to
            # fulfill the request
            part_size = min(size-len(data), len(self.readbuffer)-self.readoffset)
            if part_size < 0:
              raise AssertionError("Internal Error")
            data += self.readbuffer[self.readoffset:self.readoffset+part_size]
            self.readoffset += part_size
            return data
    except usb.core.USBError, e:
      raise JLinkError('UsbError: %s' % str(e))
    # never reached
    raise JLinkError("Internal error")

  def read_data(self, size):
    """Read data in chunks from the chip."""
    return self.read_data_bytes(size).tostring()

  def get_version(self):
    """Return the firmware version"""
    self.write_data(Array('B', [JLink.EMU_CMD_VERSION,]))
    n, = struct.unpack('<H', self.read_data(2))
    x = self.read_data(n)
    # split on nulls, get rid of empty strings
    return [s for s in x.split('\x00') if len(s)]

  # --- Private implementation -------------------------------------------

  def _wrap_api(self):
      """Deal with PyUSB API breaks"""
      import inspect
      args, varargs, varkw, defaults = \
          inspect.getargspec(usb.core.Device.read)
      if (len(args) > 2) and (args[3] == 'interface'):
          usb_api = 1  # Require "interface" parameter
      else :
          usb_api = 2
      for m in ('write', 'read'):
          setattr(self, '_%s' % m, getattr(self, '_%s_v%d' % (m, usb_api)))

  def _set_interface(self, config, ifnum):
    """Select the interface to use on the FTDI device"""
    if ifnum == 0:
      ifnum = 1
    if ifnum-1 not in xrange(config.bNumInterfaces):
      raise ValueError("No such interface for this device")
    self.index = ifnum
    self.interface = config[(ifnum-1, 0)]
    endpoints = sorted([ep.bEndpointAddress for ep in self.interface])
    self.in_ep, self.out_ep = endpoints[:2]

  def _write_v1(self, data):
    """Write to J-Link, using the deprecated API"""
    return self.usb_dev.write(self.in_ep, data, self.interface, self.usb_write_timeout)

  def _read_v1(self):
    """Read from J-Link, using the deprecated API"""
    return self.usb_dev.read(self.out_ep, self.readbuffer_chunksize, self.interface, self.usb_read_timeout)

  def _write_v2(self, data):
    """Write to J-Link, using the API introduced with pyusb 1.0.0b2"""
    return self.usb_dev.write(self.in_ep, data, self.usb_write_timeout)

  def _read_v2(self):
    """Read from J-Link, using the API introduced with pyusb 1.0.0b2"""
    return self.usb_dev.read(self.out_ep, self.readbuffer_chunksize, self.usb_read_timeout)

  def _get_max_packet_size(self):
    """Retrieve the maximum length of a data packet"""
    if not self.usb_dev:
      raise AssertionError("Device is not yet known")
    if not self.interface:
      raise AssertionError("Interface is not yet known")
    endpoint = self.interface[0]
    packet_size = endpoint.wMaxPacketSize
    return packet_size

#------------------------------------------------------------------------------

class jtag:

  def __init__(self, sn = None):
    devices = UsbTools.find_all(_jlink_vps)
    if sn is not None:
        # filter based on device serial number
        devices = [dev for dev in devices if dev[2] == sn]
    if len(devices) == 0:
        raise IOError("No such device")
    self.vid = devices[0][0]
    self.pid = devices[0][1]
    self.sn = devices[0][2]
    self.jlink = JLink()
    self.jlink.open(self.vid, self.pid, serial = self.sn)
    print self
    print self.jlink.get_version()

  def __del__(self):
    if self.jlink:
      self.jlink.close()

  def scan_ir(self, tdi, tdo = None):
    """write (and possibly read) a bit stream through the IR in the JTAG chain"""
    #self.state_x('IRSHIFT')
    #self.shift_data(tdi, tdo, self.sir_end_state)

  def scan_dr(self, tdi, tdo = None):
    """write (and possibly read) a bit stream through the DR in the JTAG chain"""
    #self.state_x('DRSHIFT')
    #self.shift_data(tdi, tdo, self.sdr_end_state)

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

