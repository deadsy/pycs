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

import time

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
    # look for any stlink device
    vps = [(vid, pid) for (vid, pid, itf) in stlink_devices]
  return usbdev.find(vps, sn)

#------------------------------------------------------------------------------

GET_VERSION            = 0xf1
DEBUG_COMMAND          = 0xf2
DFU_COMMAND            = 0xf3
GET_CURRENT_MODE       = 0xf5
GET_TARGET_VOLTAGE     = 0xf7

# dfu commands
DFU_CMD_EXIT           = 0x07

# debug commands
DBG_CMD_ENTER_JTAG     = 0x00
DBG_CMD_GETSTATUS      = 0x01
DBG_CMD_FORCEDEBUG     = 0x02
DBG_CMD_RESETSYS       = 0x03
DBG_CMD_READALLREGS    = 0x04
DBG_CMD_READREG        = 0x05
DBG_CMD_WRITEREG       = 0x06
DBG_CMD_RDMEM_32BIT    = 0x07
DBG_CMD_WRMEM_32BIT    = 0x08
DBG_CMD_RUNCORE        = 0x09
DBG_CMD_STEPCORE       = 0x0a
DBG_CMD_SETFP          = 0x0b
DBG_CMD_WRITEMEM_8BIT  = 0x0d
DBG_CMD_CLEARFP        = 0x0e
DBG_CMD_WRITEDEBUGREG  = 0x0f
DBG_CMD_ENTER          = 0x20
DBG_CMD_EXIT           = 0x21
DBG_CMD_READCOREID     = 0x22
DBG_CMD_WRDBG_32BIT    = 0x35
DBG_CMD_RDDBG_32BIT    = 0x36
DBG_CMD_ENTER_SWD      = 0xa3

#define STLINK_SWD_ENTER 0x30
#define STLINK_SWD_READCOREID 0x32  // TBD

#define STLINK_JTAG_DRIVE_NRST 0x3c

#------------------------------------------------------------------------------
# map register names to stlink register numbers

regmap = {
  'r0':0,'r1':1,'r2':2,'r3':3,'r4':4,'r5':5,'r6':6,'r7':7,
  'r8':8,'r9':9,'r10':10,'r11':11,'r12':12,'r13':13,'r14':14,'r15':15,
  'lr':14,'pc':15,'psr':16,'msp':17,'psp':18,
  # primask
  # faultmask
  # basepri
  # control
  # 19 ?
  # 20 ?
}

#------------------------------------------------------------------------------

def append_u32(x, val):
  """append a 32-bit value to a byte buffer"""
  x += Array('B', struct.pack('<I', val))

def read_u32(x):
  """read a 32-bit value from a byte buffer"""
  return struct.unpack('<I', x)[0]

#------------------------------------------------------------------------------

class stlink(object):
  """ST-Link Device Driver"""

  def __init__(self, vid, pid, sn):
    self.vid = vid
    self.pid = pid
    self.sn = sn
    itf = itf_lookup(self.vid, self.pid)
    self.usb = usbdev.usbdev()
    self.usb.open(self.vid, self.pid, interface = itf, serial = self.sn)
    # enter debug mode
    if self.get_current_mode() == 'dfu':
      self.exit_dfu_mode()
    if self.get_current_mode() != 'debug':
      self.enter_swd_mode()
    ver = self.get_version()
    assert ver['stlink_v'] == 2, 'only version 2 of stlink is supported'

  def close(self):
    self.usb.close()

  def send_recv(self, data, size):
    """send data, receive size bytes"""
    if len(data) > 0:
      self.usb.write_data(data)
    if size > 0:
      return self.usb.read_data(size)
    return None

  def get_version(self):
    """return the ST-Link version"""
    x = self.send_recv(Array('B', (GET_VERSION,)), 6)
    ver = {}
    ver['stlink_v'] = (x[0] & 0xf0) >> 4
    ver['jtag_v'] = ((x[0] & 0x0f) << 2) | ((x[1] & 0xc0) >> 6)
    ver['swim_v'] = x[1] & 0x3f
    ver['st_vid'] = (x[3] << 8) | x[2]
    ver['stlink_pid'] = (x[5] << 8) | x[4]
    return ver

  def get_target_voltage(self):
    """get target voltage in millivolts"""
    x = self.send_recv(Array('B', (GET_TARGET_VOLTAGE,)), 8)
    factor = (x[3] << 24) | (x[2] << 16) | (x[1] << 8) | (x[0] << 0)
    reading = (x[7] << 24) | (x[6] << 16) | (x[5] << 8) | (x[4] << 0)
    voltage = 2400 * reading / factor
    return voltage

  def get_current_mode(self):
    """get the current mode"""
    x = self.send_recv(Array('B', (GET_CURRENT_MODE,)), 2)
    return {0:'dfu',1:'mass',2:'debug'}.get(x[0], None)

  def get_core_id(self):
    """get the core id"""
    x = self.send_recv(Array('B', (DEBUG_COMMAND, DBG_CMD_READCOREID)), 4)
    return read_u32(x)

  def get_status(self):
    """get the status"""
    x = self.send_recv(Array('B', (DEBUG_COMMAND, DBG_CMD_GETSTATUS)), 2)
    return {0x80:'running',0x81:'halted'}.get(x[0], None)

  def exit_dfu_mode(self):
    """exit dfu command"""
    self.send_recv(Array('B', (DFU_COMMAND, DFU_CMD_EXIT)), 0)

  def enter_swd_mode(self):
    """enter swd mode"""
    self.send_recv(Array('B', (DEBUG_COMMAND, DBG_CMD_ENTER, DBG_CMD_ENTER_SWD)), 0)

  def force_debug_mode(self):
    """force debug mode"""
    self.send_recv(Array('B', (DEBUG_COMMAND, DBG_CMD_FORCEDEBUG)), 2)

  def run(self):
    """make the cpu run"""
    self.send_recv(Array('B', (DEBUG_COMMAND, DBG_CMD_RUNCORE)), 2)

  def exit_debug_mode(self):
    """exit debug mode"""
    self.send_recv(Array('B', (DEBUG_COMMAND, DBG_CMD_EXIT)), 0)

  def rd_reg(self, idx):
    """read a register value"""
    x = self.send_recv(Array('B', (DEBUG_COMMAND, DBG_CMD_READREG, idx)), 4)
    return read_u32(x)

  def rd_dbg32(self, adr):
    """read a 32-bit memory address"""
    cmd = Array('B', (DEBUG_COMMAND, DBG_CMD_RDDBG_32BIT))
    append_u32(cmd, adr)
    x = self.send_recv(cmd, 8)
    return read_u32(x[4:])

  def wr_dbg32(self, adr, val):
    """write a 32-bit memory address"""
    cmd = Array('B', (DEBUG_COMMAND, DBG_CMD_WRDBG_32BIT))
    append_u32(cmd, adr)
    append_u32(cmd, val)
    self.send_recv(cmd, 2)


  #def wr_mem32(self, adr, buf):
    #"""write 32 bit buffer to memory address"""
    #cmd = Array('B', (DEBUG_COMMAND, DEBUG_WRITEMEM_32BIT))
    #cmd += wr_uint32(adr)
    #cmd += wr_uint16(len(buf))
    #self.usb.send(cmd)
    #self.usb.send(buf)

  #def wr_mem8(self, adr, buf):
    #"""write 8 bit buffer to memory address"""
    #cmd = Array('B', (DEBUG_COMMAND, DEBUG_WRITEMEM_8BIT))
    #cmd += wr_uint32(adr)
    #cmd += wr_uint16(len(buf))
    #self.usb.send(cmd)
    #self.usb.send(buf)


  def __str__(self):
    """return a string for basic device description"""
    s = []
    s.append('ST-Link usb %04x:%04x serial %r' % (self.vid, self.pid, self.sn))
    s.append('target voltage %.3fV' % (float(self.get_target_voltage()) / 1000.0))
    return '\n'.join(s)

#------------------------------------------------------------------------------

class dbgio(object):
  """ST-Link implementation of dbgio cpu interface"""

  def __init__(self, vid = None, pid = None, idx = None, sn = None):
    """no actual operations, record the selected usb device"""
    self.vid = vid
    self.pid = pid
    self.idx = idx
    self.sn = sn
    self.cpu_name = None
    self.itf = None
    self.menu = (
      ('info', self.cmd_info),
    )

  # public functions

  def connect(self, cpu_name, itf):
    """connect the debugger to the target"""
    self.cpu_name = cpu_name
    self.dbg_itf = itf
    self.stlink = stlink(self.vid, self.pid, self.sn)
    vref = self.stlink.get_target_voltage()
    # check VREF
    assert vref > 1500, 'Vref is too low. Check target power.'

  def disconnect(self):
    """disconnect the debugger from the target"""
    self.stlink.close()

  def cmd_info(self, ui, args):
    """display stlink information"""
    ui.put('%s\n' % self)

  def is_halted(self):
    """return True if target is halted"""
    return self.stlink.get_status() == 'halted'

  def halt(self):
    """halt the cpu"""
    self.stlink.force_debug_mode()

  def go(self):
    """put the cpu into running mode"""
    self.stlink.run()

  def rdreg(self, reg):
    """read the named register"""
    idx = regmap.get(reg, None)
    if idx is None:
      return None
    return self.stlink.rd_reg(idx)

  def rd_pc(self):
    """read the program counter"""
    return self.rd_reg('pc')

  def rdmem32(self, adr, n):
    """read n 32 bit values from memory region"""
    assert adr & 3 == 0
    assert False, 'TODO'

  def rdmem16(self, adr, n):
    """read n 16 bit values from memory region"""
    assert adr & 1 == 0
    assert False, 'TODO'

  def rdmem8(self, adr, n):
    """read n 8 bit values from memory region"""
    assert False, 'TODO'

  def rd32(self, adr):
    """read 32 bit value from adr"""
    assert adr & 3 == 0
    return self.stlink.rd_dbg32(adr)

  def rd16(self, adr):
    """read 16 bit value from adr"""
    assert adr & 1 == 0
    assert False, 'TODO'

  def rd8(self, adr):
    """read 8 bit value from adr"""
    assert False, 'TODO'

  def wrmem32(self, adr, buf):
    """write buffer of 32 bit values to memory region"""
    assert adr & 3 == 0
    assert False, 'TODO'

  def wrmem16(self, adr, buf):
    """write buffer of 16 bit values to memory region"""
    assert adr & 1 == 0
    assert False, 'TODO'

  def wrmem8(self, adr, buf):
    """write buffer of 8 bit values to memory region"""
    assert False, 'TODO'

  def wr32(self, adr, val):
    """write 32 bit value to adr"""
    assert adr & 3 == 0
    return self.stlink.wr_dbg32(adr, val)

  def wr16(self, adr, val):
    """write 16 bit value to adr"""
    assert adr & 1 == 0
    assert False, 'TODO'

  def wr8(self, adr, val):
    """write 8 bit value to adr"""
    assert False, 'TODO'

  def __str__(self):
    s = []
    s.append(str(self.stlink))
    return '\n'.join(s)

#------------------------------------------------------------------------------
