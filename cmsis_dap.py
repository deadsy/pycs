#------------------------------------------------------------------------------
"""

CMSIS-DAP Driver

"""
#------------------------------------------------------------------------------

#import struct
from array import array as Array

#import usbdev
#import cortexm
#import iobuf

import hid

#------------------------------------------------------------------------------
# supported devices

# these are the cmsis-dap devices we know about (vid, pid, itf)
known_devices = (
  (0x0d28, 0x0204, 3), # NXP MIMXRT1020-EVK
)

def itf_lookup(vid, pid):
  """return the interface to use for a given device"""
  for (v, p, i) in known_devices:
    if (v == vid) and (p == pid):
      return i
  return None

def find(sn=None):
  """find the cmsis-dap device, the serial number is used to uniqify the match"""
  # get the set of HIDs
  hid_devices = hid.enumerate()
  # find cmsis-dap devices
  devices = []
  for (vid, pid, _) in known_devices:
    for dev in hid_devices:
      # filter out devices that don't match
      if vid != dev['vendor_id']:
        continue
      if pid != dev['product_id']:
        continue
      if sn is not None and sn != dev['serial_number']:
        continue
      # we have a match
      devices.append(dev)
  return devices

#------------------------------------------------------------------------------
# cmsis-dap protocol constants

# CMSIS-DAP General Commands
CMD_DAP_INFO = 0x00
CMD_DAP_LED = 0x01
CMD_DAP_CONNECT = 0x02
CMD_DAP_DISCONNECT = 0x03
CMD_DAP_WRITE_ABORT = 0x08
CMD_DAP_DELAY = 0x09
CMD_DAP_RESET_TARGET = 0x0A

# DAP_CMD_INFO
INFO_ID_VID = 0x01            # Get the Vendor ID (string)
INFO_ID_PID = 0x02            # Get the Product ID (string)
INFO_ID_SN = 0x03             # Get the Serial Number (string)
INFO_ID_FW_VERSION = 0x04     # Get the CMSIS-DAP Firmware Version (string)
INFO_ID_VENDOR_NAME = 0x05    # Get the Target Device Vendor (string)
INFO_ID_DEVICE_NAME = 0x06    # Get the Target Device Name (string)
INFO_ID_DBG_CAPS = 0xF0       # Get information about the Capabilities (BYTE) of the Debug Unit
INFO_ID_TDT_PARMS = 0xF1      # Get the Test Domain Timer parameter information
INFO_ID_SWO_TRACE_SIZE = 0xFD # Get the SWO Trace Buffer Size (WORD)
INFO_ID_MAX_PKT_COUNT = 0xFE  # Get the maximum Packet Count (BYTE)
INFO_ID_MAX_PKT_SIZE = 0xFF   # Get the maximum Packet Size (SHORT)

# DAP Status Code
DAP_OK = 0
DAP_ERROR = 0xFF

#------------------------------------------------------------------------------
# map register names to cmsis-dap register numbers

regmap = {
  'r0':0, 'r1':1, 'r2':2, 'r3':3, 'r4':4, 'r5':5, 'r6':6, 'r7':7,
  'r8':8, 'r9':9, 'r10':10, 'r11':11, 'r12':12, 'r13':13, 'r14':14, 'r15':15,
  'lr':14, 'pc':15, 'psr':16, 'msp':17, 'psp':18,
  # primask
  # faultmask
  # basepri
  # control
  # 19 ?
  # 20 ?
}

def dump_buf(x):
  s = []
  for c in x:
    s.append('%02x' % c)
  print(' '.join(s))

#------------------------------------------------------------------------------

class dap:
  """CMSIS-DAP Device Driver"""

  def __init__(self, dev):
    self.vid = dev['vendor_id']
    self.pid = dev['product_id']
    self.sn = dev['serial_number']
    self.hid = hid.Device(self.vid, self.pid, self.sn)
    self.pkt_size = 64
    self.pkt_size = self.get_info_short(INFO_ID_MAX_PKT_SIZE)
    self.pkt_count = self.get_info_byte(INFO_ID_MAX_PKT_COUNT)
    self.ver = self.get_info_string(INFO_ID_FW_VERSION)
    self.caps = self.get_info_byte(INFO_ID_DBG_CAPS)

    print('ver %s' % self.ver)
    print('caps %d' % self.caps)
    print('pkt_count %d' % self.pkt_count)
    print('pkt_size %d' % self.pkt_size)

    #     |  close(self)
    #     |  get_feature_report(self, report_id, size)
    #     |  get_indexed_string(self, index, max_length=255)
    #     |  read(self, size, timeout=None)
    #     |  send_feature_report(self, data)
    #     |  write(self, data)

  def __del__(self):
    self.close()

  def close(self):
    """close the HID"""
    self.hid.close()

  def xfer(self, tx):
    """tx and rx some bytes to the HID"""
    self.hid.write(tx)
    return self.hid.read(self.pkt_size + 1)

  def cmd_dap_info(self, id):
    rx = self.xfer(bytes((0, CMD_DAP_INFO, id)))
    return rx[1:]

  def get_info_string(self, info):
    """get an information string from the debugger"""
    rx = self.cmd_dap_info(info)
    n = rx[0]
    if n:
      return rx[1:n].decode("utf-8")
    return None

  def get_info_byte(self, info):
    """get an information byte/u8 from the debugger"""
    rx = self.cmd_dap_info(info)
    if rx[0] == 1:
      return rx[1]
    return None

  def get_info_short(self, info):
    """get an information short/u16 from the debugger"""
    rx = self.cmd_dap_info(info)
    if rx[0] == 2:
      return rx[1] + (rx[2] << 8)
    return None

  def get_info_word(self, info):
    """get an information word/u32 from the debugger"""
    rx = self.cmd_dap_info(info)
    if rx[0] == 4:
      return rx[1] + (rx[2] << 8) + (rx[3] << 16) + (rx[4] << 24)
    return None

  def led_ctrl(self, val):
    """control the debugger leds"""
    rx = self.xfer(bytes((0, CMD_DAP_LED, 0, val)))
    assert rx[1] == 0

  def dap_connect(self, mode):
    rx = self.xfer(bytes((0, CMD_DAP_CONNECT, mode)))
    assert rx[1] == mode

  def dap_disconnect(self):
    rx = self.xfer(bytes((0, CMD_DAP_DISCONNECT)))
    assert rx[1] == DAP_OK




  #def DAP_HostStatus(self):
  #def DAP_Connect(self):
  #def DAP_Disconnect(self):
  #def DAP_WriteABORT(self):
  #def DAP_Delay(self):
  #def DAP_ResetTarget(self):

  #def DAP_SWJ_Pins(self):
  #def DAP_SWJ_Clock(self):
  #def DAP_SWJ_Sequence(self):

  #def DAP_SWD_Configure(self):
  #def DAP_SWD_Sequence(self):

  #def DAP_SWO_Transport(self):
  #def DAP_SWO_Mode(self):
  #def DAP_SWO_Baudrate(self):
  #def DAP_SWO_Control(self):
  #def DAP_SWO_Status(self):
  #def DAP_SWO_ExtendedStatus(self):
  #def DAP_SWO_Data(self):

  #def DAP_JTAG_Sequence(self):
  #def DAP_JTAG_Configure(self):
  #def DAP_JTAG_IDCODE(self):

  #def DAP_TransferConfigure(self):
  #def DAP_Transfer(self):
  #def DAP_TransferBlock(self):
  #def DAP_TransferAbort(self):
  #def DAP_ExecuteCommands(self):
  #def DAP_QueueCommands(self):

  def rd_reg(self, n):
    """read from a register"""
    # TODO
    return 0

  def wr_reg(self, n, val):
    """write to a register"""
    # TODO

  def rd_mem8(self, adr, n):
    """read n 8-bit values from memory region"""
    # TODO
    return [0 for i in range(n)]

  def rd_mem16(self, adr, n):
    """read n 16-bit values from memory region"""
    assert adr & 1 == 0
    # TODO
    return [0 for i in range(n)]

  def rd_mem32(self, adr, n):
    """read n 32-bit values from memory region"""
    assert adr & 3 == 0
    # TODO
    return [0 for i in range(n)]

  def __str__(self):
    """return a string for basic device description"""
    s = []
    s.append('CMSIS-DAP')
    s.append('%04x:%04x' % (self.vid, self.pid))
    s.append('version %s' % self.ver)
    s.append('serial %r' % self.sn)
    return ' '.join(s)

#------------------------------------------------------------------------------

class dbgio:
  """CMSIS-DAP implementation of dbgio cpu interface"""

  def __init__(self, dev):
    self.dev = dev
    self.cpu_name = None
    self.menu = (
      ('info', self.cmd_info),
    )

  def connect(self, cpu_name, itf):
    """connect the debugger to the target"""
    self.cpu_name = cpu_name
    self.dbg_itf = itf
    self.dap = dap(self.dev)

  def disconnect(self):
    """disconnect the debugger from the target"""
    self.dap.close()

  def cmd_info(self, ui, args):
    """display cmsis-dap information"""
    ui.put('%s\n' % self)

  def is_halted(self):
    """return True if target is halted"""
    # TODO
    return True

  def rdreg(self, reg):
    """read from the named register"""
    n = regmap.get(reg, None)
    if n is None:
      return None
    return self.dap.rd_reg(n)

  def wrreg(self, reg, val):
    """write to the named register"""
    n = regmap.get(reg, None)
    if n is None:
      return
    self.dap.wr_reg(n, val)

  def rdmem32(self, adr, n, io):
    """read n 32-bit words from memory starting at adr"""
    max_n = 0x20
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      _ = [io.wr32(x) for x in self.dap.rd_mem32(adr, nread)]
      n -= nread
      adr += nread * 4

  def rdmem16(self, adr, n, io):
    """read n 16-bit words from memory starting at adr"""
    max_n = 0x20
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      _ = [io.wr16(x) for x in self.dap.rd_mem16(adr, nread)]
      n -= nread
      adr += nread * 2

  def rdmem8(self, adr, n, io):
    """read n 8-bit words from memory starting at adr"""
    # n = 0..0x3c (ok), 0x3d..0x40 (slow), >= 0x41 (fails)
    max_n = 0x20
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      _ = [io.wr8(x) for x in self.dap.rd_mem8(adr, nread)]
      n -= nread
      adr += nread

  def rdmem(self, adr, n, io):
    """read a buffer from memory starting at adr"""
    if io.has_wr(32):
      self.rdmem32(adr, n, io)
    elif io.has_wr(16):
      self.rdmem16(adr, n, io)
    elif io.has_wr(8):
      self.rdmem8(adr, n, io)
    else:
      assert False, 'bad buffer width'

  def rd32(self, adr):
    """read 32 bit value from adr"""
    return self.dap.rd_mem32(adr, 1)[0]

  def rd16(self, adr):
    """read 16 bit value from adr"""
    return self.dap.rd_mem16(adr, 1)[0]

  def rd8(self, adr):
    """read 8 bit value from adr"""
    return self.dap.rd_mem8(adr, 1)[0]

  def __str__(self):
    return str(self.dap)


#------------------------------------------------------------------------------
