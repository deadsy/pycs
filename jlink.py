# ----------------------------------------------------------------------------

import sys
import time
import os
import ctypes
import struct

from ctypes import c_uint32, c_int, c_void_p

# ----------------------------------------------------------------------------
# target interface

_JLINKARM_TIF_JTAG = 0
_JLINKARM_TIF_SWD = 1
_JLINKARM_TIF_BDM3 = 2
_JLINKARM_TIF_FINE = 3
_JLINKARM_TIF_ICSP = 4
_JLINKARM_TIF_SPI = 5
_JLINKARM_TIF_C2 = 6

# ----------------------------------------------------------------------------
# map register names to jlink register numbers

regmap = {
  'r0':0,'r1':1,'r2':2,'r3':3,'r4':4,'r5':5,'r6':6,'r7':7,
  'r8':8,'r9':9,'r10':10,'r11':11,'r12':12,'r13':13,'r14':14,'r15':15,
  'lr':14,'pc':15,'psr':16,'msp':13,
  # psp
  # primask
  # faultmask
  # basepri
  # control
}

# ----------------------------------------------------------------------------
# map from SVD cpu names to JLink cpu names

cpu_names = {
  'CM0': 'cortex-m4',
  'CM0PLUS': 'cortex-m0+',
  'CM0+': 'cortex-m0+',
  'CM1': 'cortex-m1',
  'SC000': '',
  'CM3': 'cortex-m3',
  'SC300': '',
  'CM4': 'cortex-m4',
  'CM7': 'cortex-m7',
  'CA5': 'cortex-a5',
  'CA7': 'cortex-a7',
  'CA8': 'cortex-a8',
  'CA9': 'cortex-a9',
  'CA15': 'cortex-a15',
  'CA17': 'cortex-a17',
  'CA53': 'cortex-a53',
  'CA57': 'cortex-a57',
  'CA72': 'cortex-a72',
}

# ----------------------------------------------------------------------------

class JLinkException(Exception):
  pass

# ----------------------------------------------------------------------------

def locate_library(libname, paths=sys.path, loader=None):
  if loader is None:
    loader = ctypes.cdll  # windll
  for path in paths:
    if path.lower().endswith('.zip'):
      path = os.path.dirname(path)
    library = os.path.join(path, libname)
    sys.stderr.write('trying %r...\n' % library)
    if os.path.exists(library):
      sys.stderr.write('using %r\n' % library)
      return loader.LoadLibrary(library), library
  else:
    raise IOError('%s not found' % libname)

def get_jlink_dll():
  # what kind of system am I?
  import platform
  if platform.architecture()[0] == '32bit':
    libpath = 'lib32'
  elif platform.architecture()[0] == '64bit':
    libpath = 'lib64'
  else:
    libpath = ''
    raise Exception(repr(platform.architecture()))

  # start with the script path
  search_path = [os.path.join(os.path.dirname(
      os.path.realpath(__file__)), libpath)]
  search_path += sys.path[:]  # copy sys.path list

  # if environment variable is set, insert this path first
  try:
    search_path.insert(0, os.environ['JLINK_PATH'])
  except KeyError:
    try:
      search_path.extend(os.environ['PATH'].split(os.pathsep))
    except KeyError:
      pass

  if sys.platform == 'win32':
    jlink, backend_info = locate_library('jlinkarm.dll', search_path)
  elif sys.platform == 'linux2':
    jlink, backend_info = locate_library(
        'libjlinkarm.so.5', search_path, ctypes.cdll)
  elif sys.platform == 'darwin':
    jlink, backend_info = locate_library(
        'libjlinkarm.so.5.dylib', search_path, ctypes.cdll)
  return jlink, backend_info

# ----------------------------------------------------------------------------

class JLink(object):

  def __init__(self, idx = 0):
    self.usb_idx = idx
    # load the library
    self.jl, self.jlink_lib_name = get_jlink_dll()
    self.select_usb(self.usb_idx)
    self.jlink_open()

  def get_dll_version(self):
    # int JLINKARM_GetDLLVersion(void);
    fn = self.jl.JLINKARM_GetDLLVersion
    fn.restype = ctypes.c_int
    fn.argtypes = []
    return fn()

  def get_compile_data_time(self):
    # char *JLINKARM_GetCompileDateTime(void);
    fn = self.jl.JLINKARM_GetCompileDateTime
    fn.restype = ctypes.c_char_p
    fn.argtypes = []
    return fn()

  def select_usb(self, port):
    # uint8_t JLINKARM_SelectUSB(long int port);
    fn = self.jl.JLINKARM_SelectUSB
    fn.restype = ctypes.c_ubyte
    fn.argtypes = [ctypes.c_long, ]
    return fn(ctypes.c_long(port))

  def jlink_open(self):
    # long int JLINKARM_Open(void);
    fn = self.jl.JLINKARM_Open
    fn.restype = ctypes.c_long
    fn.argtypes = []
    rc = fn()
    if rc != 0:
      raise JLinkException('JLINKARM_Open returned %d' % rc)

  def jlink_close(self):
    # void JLINKARM_Close(void);
    fn = self.jl.JLINKARM_Close
    fn.restype = None
    fn.argtypes = []
    fn()

  def get_fw_string(self):
    # int JLINKARM_GetFirmwareString(char *str, int n);
    fn = self.jl.JLINKARM_GetFirmwareString
    fn.restype = ctypes.c_int
    fn.argtypes = [ctypes.c_char_p, ctypes.c_int]
    buf = ctypes.create_string_buffer(128)
    fn(buf, len(buf))
    return buf.value

  def get_hw_version(self):
    # long int JLINKARM_GetHardwareVersion(void);
    fn = self.jl.JLINKARM_GetHardwareVersion
    fn.restype = ctypes.c_long
    fn.argtypes = []
    return fn()

  def get_sn(self):
    # long int JLINKARM_GetSN(void);
    fn = self.jl.JLINKARM_GetSN
    fn.restype = ctypes.c_long
    fn.argtypes = []
    return fn()

  def get_hw_status(self):
    # void JLINKARM_GetHWStatus(JTAG_HW_STATUS * pStat);
    fn = self.jl.JLINKARM_GetHWStatus
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p,]
    n = 8
    buf = (ctypes.c_uint8 * n)()
    fn(ctypes.byref(buf))
    # This is *probably* a passthrough of the dongles
    # EMU_CMD_GET_STATE operation. The Vref looks good.
    # The other values could be tested more.
    x = struct.unpack('<HBBBBBB', buf)
    state = {}
    state['vref'] = x[0]
    state['tck'] = x[1]
    state['tdi'] = x[2]
    state['tdo'] = x[3]
    state['tms'] = x[4]
    state['srst'] = x[5]
    state['trst'] = x[6]
    return state

  def exec_command(self, cmd):
    # int JLINKARM_ExecCommand(char *sIn, char *sBuffer, int buffersize);
    fn = self.jl.JLINKARM_ExecCommand
    fn.restype = ctypes.c_int
    fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    command = ctypes.create_string_buffer(cmd)
    result = ctypes.create_string_buffer(128)
    rc = fn(command, result, len(result))
    if rc != 0:
      raise JLinkException('JLINKARM_ExecCommand returned %d' % rc)
    return result.value

  def set_speed(self, khz):
    # void JLINKARM_SetSpeed(long int khz);
    fn = self.jl.JLINKARM_SetSpeed
    fn.restype = None
    fn.argtypes = [ctypes.c_long, ]
    fn(ctypes.c_long(khz))

  def tif_select(self, tif):
    # int JLINKARM_TIF_Select(int intface);
    fn = self.jl.JLINKARM_TIF_Select
    fn.restype = ctypes.c_int
    fn.argtypes = [ctypes.c_int, ]
    rc = fn(ctypes.c_int(tif))
    if rc != 0:
      raise JLinkException('JLINKARM_TIF_Select returned %d' % rc)

  def jlink_connect(self):
    # int JLINKARM_Connect(void);
    fn = self.jl.JLINKARM_Connect
    fn.restype = ctypes.c_int
    fn.argtypes = []
    rc = fn()
    if rc != 0:
      raise JLinkException('JLINKARM_Connect returned %d' % rc)

  def halt(self):
    # int JLINKARM_Halt(void);
    fn = self.jl.JLINKARM_Halt
    fn.restype = ctypes.c_int
    fn.argtypes = []
    rc = fn()
    if rc != 0:
      raise JLinkException('JLINKARM_Halt returned %d' % rc)

  def is_halted(self):
    # int JLINKARM_IsHalted(void);
    fn = self.jl.JLINKARM_IsHalted
    fn.restype = ctypes.c_int
    fn.argtypes = []
    return fn() != 0

  def go(self):
    # void JLINKARM_Go(void);
    fn = self.jl.JLINKARM_Go
    fn.restype = None
    fn.argtypes = []
    fn()

  def reset(self):
    # void JLINKARM_Reset(void);
    fn = self.jl.JLINKARM_Reset
    fn.restype = None
    fn.argtypes = []
    fn()

  def step(self):
    # char JLINKARM_Step(void);
    fn = self.jl.JLINKARM_Step
    fn.restype = ctypes.c_uint8
    fn.argtypes = []
    return fn()

  def rdreg(self, reg):
    # uint32_t JLINKARM_ReadReg(int reg);
    fn = self.jl.JLINKARM_ReadReg
    fn.restype = ctypes.c_uint32
    fn.argtypes = [ctypes.c_int]
    return fn(ctypes.c_int(idx))

  def cp15_is_present(self):
    # int JLINKARM_CP15_IsPresent(void);
    fn = self.jl.JLINKARM_CP15_IsPresent
    fn.restype = ctypes.c_int
    fn.argtypes = []
    return fn() != 0

  def rd_cp15(self, crn, op1, crm, op2):
    # int JLINKARM_CP15_ReadEx(uint32_t crn, uint32_t crm, uint32_t op1, uint32_t op2, uint32_t *val)
    fn = self.jl.JLINKARM_CP15_ReadEx
    fn.restype = c_int
    fn.argtypes = [c_uint32,c_uint32,c_uint32,c_uint32,c_void_p]
    val = c_uint32()
    rc = fn(c_uint32(crn), c_uint32(crm), c_uint32(op1), c_uint32(op2), ctypes.byref(val))
    assert rc == 0, 'JLINKARM_CP15_ReadEx returned %d' % rc
    return val.value

  def wr_cp15(self, crn, op1, crm, op2, val):
    # int JLINKARM_CP15_WriteEx(uint32_t crn, uint32_t crm, uint32_t op1, uint32_t op2, uint32_t val)
    fn = self.jl.JLINKARM_CP15_WriteEx
    fn.restype = c_int
    fn.argtypes = [c_uint32,c_uint32,c_uint32,c_uint32,c_uint32]
    rc = fn(c_uint32(crn), c_uint32(crm), c_uint32(op1), c_uint32(op2), c_uint32(val))
    assert rc == 0, 'JLINKARM_CP15_WriteEx returned %d' % rc

  def rdmem32(self, base, n):
    # void JLINKARM_ReadMemU32(uint32_t addr, uint32_t n, uint32_t *data, uint8_t *status);
    fn = self.jl.JLINKARM_ReadMemU32
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
    status = ctypes.c_ubyte()
    buf = (ctypes.c_uint32 * n)()
    fn(ctypes.c_uint32(base), ctypes.c_uint32(n), ctypes.byref(buf), ctypes.byref(status))
    if status.value != 0:
      raise JLinkException('JLINKARM_ReadMemU32 status = %d (0x%08x)' % (status.value, base))
    return [buf[i] for i in range(n)]

  def rdmem16(self, base, n):
    # void JLINKARM_ReadMemU16(uint32_t addr, uint32_t n, uint16_t *data, uint8_t *status);
    fn = self.jl.JLINKARM_ReadMemU16
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
    status = ctypes.c_ubyte()
    buf = (ctypes.c_uint16 * n)()
    fn(ctypes.c_uint32(base), ctypes.c_uint32(n), ctypes.byref(buf), ctypes.byref(status))
    if status.value != 0:
      raise JLinkException('JLINKARM_ReadMemU16 status = %d (0x%08x)' % (status.value, base))
    return [buf[i] for i in range(n)]

  def rdmem8(self, base, n):
    # void JLINKARM_ReadMemU8(uint32_t addr, uint32_t n, uint8_t *data, uint8_t *status);
    fn = self.jl.JLINKARM_ReadMemU8
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
    status = ctypes.c_ubyte()
    buf = (ctypes.c_uint8 * n)()
    fn(ctypes.c_uint32(base), ctypes.c_uint32(n), ctypes.byref(buf), ctypes.byref(status))
    if status.value != 0:
      raise JLinkException('JLINKARM_ReadMemU8 status = %d (0x%08x)' % (status.value, base))
    return [buf[i] for i in range(n)]

  def wrmem32(self, adr, buf):
    """write a buffer of 32 bit values to a memory region"""
    # void JLINKARM_WriteMem(U32 addr, U32 count, const void * p);

    # Note1: I'm not sure what the underlying store is for JLINKARM_WriteMem.
    # It stores an arbitrary number of bytes without overwriting adjacent memory locations,
    # but does it do 32 bit stores when it can? I'm not sure. If you want to ensure 8/16/32
    # stores then the JLINKARM_WriteU8/16/32 calls might be a better bet. But I'm not sure
    # how they work either.

    # Note2: I use JLINKARM_WriteMem for writing nand page data to the controller cache.
    # It works and is much faster than doing individual calls to JLINKARM_WriteU32.

    fn = self.jl.JLINKARM_WriteMem
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    n = len(buf)
    cbuf = (ctypes.c_uint32 * n)()
    cbuf[:] = buf
    fn(ctypes.c_uint32(adr), ctypes.c_uint32(n * 4), ctypes.byref(cbuf))

  def wrmem16(self, adr, buf):
    """write a buffer of 16 bit values to a memory region"""
    # void JLINKARM_WriteMem(U32 addr, U32 count, const void * p);
    fn = self.jl.JLINKARM_WriteMem
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    n = len(buf)
    cbuf = (ctypes.c_uint16 * n)()
    cbuf[:] = buf
    fn(ctypes.c_uint32(adr), ctypes.c_uint32(n * 2), ctypes.byref(cbuf))

  def wrmem8(self, adr, buf):
    """write a buffer of 8 bit values to a memory region"""
    # void JLINKARM_WriteMem(U32 addr, U32 count, const void * p);
    fn = self.jl.JLINKARM_WriteMem
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    n = len(buf)
    cbuf = (ctypes.c_uint8 * n)()
    cbuf[:] = buf
    fn(ctypes.c_uint32(adr), ctypes.c_uint32(n), ctypes.byref(cbuf))

  def wr32(self, adr, val):
    # void JLINKARM_WriteU32(uint32_t addr, uint32_t val);
    fn = self.jl.JLINKARM_WriteU32
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    fn(ctypes.c_uint32(adr), ctypes.c_uint32(val))

  def wr16(self, adr, val):
    # void JLINKARM_WriteU16(uint32_t addr, uint16_t val);
    fn = self.jl.JLINKARM_WriteU16
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint16]
    fn(ctypes.c_uint32(adr), ctypes.c_uint16(val))

  def wr8(self, adr, val):
    # void JLINKARM_WriteU8(uint32_t addr, uint8_t val);
    fn = self.jl.JLINKARM_WriteU8
    fn.restype = None
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint8]
    fn(ctypes.c_uint32(adr), ctypes.c_uint8(val))

  def __str__(self):
    s = []
    s.append('jlink library v%d %s' % (self.get_dll_version(), self.get_compile_data_time()))
    s.append('jlink device v%d sn%d %s' % (self.get_hw_version(), self.get_sn(), self.get_fw_string()))
    s.append('target voltage %.3fV' % (float(self.get_hw_status()['vref']) / 1000.0))
    return '\n'.join(s)

# ----------------------------------------------------------------------------

class dbgio(object):
  """JLink implementation of dbgio cpu interface"""

  def __init__(self, idx = 0):
    """no actual operations, record the selected usb device"""
    self.usb_idx = idx
    self.menu = (
      ('info', self.cmd_info),
    )

  def connect(self, cpu_name, itf):
    """connect the debugger to the target"""
      # create the jlink interface
    self.jlink = JLink(self.usb_idx)
    # check the hardware
    state = self.jlink.get_hw_status()
    assert state['vref'] > 1500, 'Vref is too low. Check target power.'
    assert state['srst'] == 1, '~SRST signal is asserted. Target is held in reset.'
    # setup the jlink interface
    self.jlink.exec_command('device=%s' % cpu_names[cpu_name])
    self.jlink.set_speed(4000)
    itf = {'swd':_JLINKARM_TIF_SWD,'jtag':_JLINKARM_TIF_JTAG}[itf]
    self.jlink.tif_select(itf)
    self.jlink.jlink_connect()

  def disconnect(self):
    """disconnect the debugger from the target"""
    self.jlink.jlink_close()

  def cmd_info(self, ui, args):
    """display jlink information"""
    ui.put('%s\n' % self)

  def is_halted(self):
    """return True if target is halted"""
    return self.jlink.is_halted()

  def halt(self):
    """halt the cpu"""
    self.jlink.halt()

  def go(self):
    """put the cpu into running mode"""
    self.jlink.go()

  def rdreg(self, reg):
    """read the named register"""
    n = regmap.get(reg, None)
    if n is None:
      return None
    return self.jlink.rdreg(n)

  def rdmem32(self, adr, n, io):
    """read n 32-bit values from memory region"""
    max_n = 16
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      [io.wr32(x) for x in self.jlink.rdmem32(adr, nread)]
      n -= nread
      adr += nread * 4

  def rdmem16(self, adr, n, io):
    """read n 16-bit values from memory region"""
    max_n = 32
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      [io.wr16(x) for x in self.jlink.rdmem16(adr, nread)]
      n -= nread
      adr += nread * 2

  def rdmem8(self, adr, n, io):
    """read n 8-bit values from memory region"""
    max_n = 64
    while n > 0:
      nread = (n, max_n)[n >= max_n]
      [io.wr8(x) for x in self.jlink.rdmem8(adr, nread)]
      n -= nread
      adr += nread

  def wrmem32(self, adr, n, io):
    """write n 32-bit words to memory starting at adr"""
    self.jlink.wrmem32(adr, [io.rd32() for i in range(n)])

  def wrmem16(self, adr, n, io):
    """write n 16-bit words to memory starting at adr"""
    self.jlink.wrmem16(adr, [io.rd16() for i in range(n)])

  def wrmem8(self, adr, n, io):
    """write n 8-bit words to memory starting at adr"""
    self.jlink.wrmem8(adr, [io.rd8() for i in range(n)])

  def rd32(self, adr):
    """read 32 bit value from adr"""
    return self.jlink.rdmem32(adr, 1)[0]

  def rd16(self, adr):
    """read 16 bit value from adr"""
    return self.jlink.rdmem16(adr, 1)[0]

  def rd8(self, adr):
    """read 8 bit value from adr"""
    return self.jlink.rdmem8(adr, 1)[0]

  def wr32(self, adr, val):
    """write 32 bit value to adr"""
    return self.jlink.wr32(adr, val)

  def wr16(self, adr, val):
    """write 16 bit value to adr"""
    return self.jlink.wr16(adr, val)

  def wr8(self, adr, val):
    """write 8 bit value to adr"""
    return self.jlink.wr8(adr, val)

  def __str__(self):
    return str(self.jlink)

# ----------------------------------------------------------------------------
