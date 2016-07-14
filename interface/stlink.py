#!/usr/bin/python

#------------------------------------------------------------------------------
"""

ST-Link Driver

"""
#------------------------------------------------------------------------------

import usb.core
import usb.util

from usbtools.usbtools import UsbTools
from array import array as Array

#------------------------------------------------------------------------------

_stlink_vps = (
  (0x0483, 0x3744), # Version 1
  (0x0483, 0x3748), # Version 2
  (0x0483, 0x374B), # Version 2.1
)

#------------------------------------------------------------------------------

class ST_Link_Error(IOError):
  """Communication error with the ST-Link device"""

class ST_Link(object):
  """ST-Link Device Driver"""

  GET_VERSION = 0xF1
  DEBUG_COMMAND = 0xF2
  DFU_COMMAND = 0xF3
  SWIM_COMMAND = 0xF4
  GET_CURRENT_MODE = 0xF5
  GET_TARGET_VOLTAGE = 0xF7

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

  def open(self, vendor, product, interface=1, index=0, serial=None, description=None):
    """Open a new interface to the specified ST-Link device"""
    self.usb_dev = UsbTools.get_device(vendor, product, index, serial, description)
    config = self.usb_dev.get_active_configuration()
    # detect invalid interface as early as possible
    if interface > config.bNumInterfaces:
      raise ST_Link_Error('No such ST-Link port: %d' % interface)
    self._set_interface(config, interface)
    self.max_packet_size = self._get_max_packet_size()

#    self.caps = self.get_capabilities()
    # work out which HW_JTAG command to used
#    ver = self.get_hw_version()
#    self.hw_jtag_cmd = (JLink.EMU_CMD_HW_JTAG2, JLink.EMU_CMD_HW_JTAG3)[ver['major'] >= 5]

  def close(self):
    """Close the ST-Link interface"""
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
          raise ST_Link_Error("Usb bulk write error")
        offset += length
      return offset
    except usb.core.USBError, e:
      raise ST_Link_Error('UsbError: %s' % str(e))

  def read_data(self, size, attempt=1):
    """Read data in chunks from the chip."""
    # Packet size sanity check
    if not self.max_packet_size:
      raise ST_Link_Error("max_packet_size is bogus")
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
      raise ST_Link_Error('UsbError: %s' % str(e))
    # never reached
    raise ST_Link_Error("Internal error")


  def get_version(self):
    """return the ST-Link version"""
    self.write_data(Array('B', [ST_Link.GET_VERSION,]))
    x = self.read_data(6)
    print x

  # private functions

  def _wrap_api(self):
    """Deal with PyUSB API breaks"""
    import inspect
    args, varargs, varkw, defaults = inspect.getargspec(usb.core.Device.read)
    if (len(args) > 2) and (args[3] == 'interface'):
      usb_api = 1  # Require "interface" parameter
    else :
      usb_api = 2
    for m in ('write', 'read'):
      setattr(self, '_%s' % m, getattr(self, '_%s_v%d' % (m, usb_api)))

  def _set_interface(self, config, ifnum):
    """Select the interface to use on the ST-Link device"""
    if ifnum == 0:
      ifnum = 1
    if ifnum-1 not in xrange(config.bNumInterfaces):
      raise ValueError("No such interface for this device")
    self.index = ifnum
    self.interface = config[(ifnum-1, 0)]
    endpoints = sorted([ep.bEndpointAddress for ep in self.interface])
    self.in_ep, self.out_ep = endpoints[:2]

  def _get_max_packet_size(self):
    """Retrieve the maximum length of a data packet"""
    if not self.usb_dev:
      raise AssertionError("Device is not yet known")
    if not self.interface:
      raise AssertionError("Interface is not yet known")
    endpoint = self.interface[0]
    packet_size = endpoint.wMaxPacketSize
    return packet_size

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

#------------------------------------------------------------------------------

class stlink_driver(object):

  def __init__(self, sn = None):
    devices = UsbTools.find_all(_stlink_vps)
    if sn is not None:
        # filter based on device serial number
        devices = [dev for dev in devices if dev[2] == sn]
    if len(devices) == 0:
        raise IOError("No such device")
    self.vid = devices[0][0]
    self.pid = devices[0][1]
    self.sn = devices[0][2]
    self.stlink = ST_Link()
    self.stlink.open(self.vid, self.pid, serial = self.sn)
    self.stlink.get_version()

  def __del__(self):
    """close the ST-Link interface"""
    if self.stlink:
      self.stlink.close()

  def __str__(self):
    s = []
    s.append('ST-Link %04x:%04x serial %r' % (self.vid, self.pid, self.sn))
    return ', '.join(s)

#------------------------------------------------------------------------------

if __name__ == '__main__':
  x = stlink_driver()
  print x

#------------------------------------------------------------------------------
"""

sudo st-util -v99
2016-07-14T08:11:34 DEBUG src/stlink-common.c: stlink current mode: mass
2016-07-14T08:11:34 DEBUG src/stlink-common.c: stlink current mode: mass
2016-07-14T08:11:34 DEBUG src/stlink-common.c: *** stlink_enter_swd_mode ***
2016-07-14T08:11:34 DEBUG src/stlink-common.c: *** looking up stlink version
2016-07-14T08:11:34 DEBUG src/stlink-common.c: st vid         = 0x0483 (expect 0x0483)
2016-07-14T08:11:34 DEBUG src/stlink-common.c: stlink pid     = 0x3748
2016-07-14T08:11:34 DEBUG src/stlink-common.c: stlink version = 0x2
2016-07-14T08:11:34 DEBUG src/stlink-common.c: jtag version   = 0xe
2016-07-14T08:11:34 DEBUG src/stlink-common.c: swim version   = 0x0
2016-07-14T08:11:34 DEBUG src/stlink-common.c:     notice: the firmware doesn't support a swim interface
2016-07-14T08:11:34 INFO src/stlink-common.c: Loading device parameters....
2016-07-14T08:11:34 DEBUG src/stlink-common.c: *** stlink_core_id ***
2016-07-14T08:11:34 DEBUG src/stlink-common.c: core_id = 0x2ba01477
2016-07-14T08:11:34 DEBUG src/stlink-common.c: *** stlink_read_debug32 10016413 is 0xe0042000
2016-07-14T08:11:34 DEBUG src/stlink-common.c: *** stlink_read_debug32 400c000 is 0x1fff7a20
2016-07-14T08:11:34 INFO src/stlink-common.c: Device connected is: F4 device, id 0x10016413
2016-07-14T08:11:34 INFO src/stlink-common.c: SRAM size: 0x30000 bytes (192 KiB), Flash: 0x100000 bytes (1024 KiB) in pages of 16384 bytes
2016-07-14T08:11:34 DEBUG src/stlink-common.c: *** stlink_reset ***
2016-07-14T08:11:34 INFO gdbserver/gdb-server.c: Chip ID is 00000413, Core ID is  2ba01477.
2016-07-14T08:11:34 DEBUG src/stlink-common.c: *** reading target voltage
2016-07-14T08:11:34 DEBUG src/stlink-common.c: target voltage = 2915mV
2016-07-14T08:11:34 INFO gdbserver/gdb-server.c: Target voltage is 2915 mV.
2016-07-14T08:11:34 INFO gdbserver/gdb-server.c: Listening at *:4242...

"""
#------------------------------------------------------------------------------






