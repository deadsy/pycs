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
# registers

REG_R0 = 0
REG_R1 = 1
REG_R2 = 2
REG_R3 = 3
REG_R4 = 4
REG_R5 = 5
REG_R6 = 6
REG_R7 = 7
REG_CPSR = 8
REG_R15_PC = 9
REG_R8_USR = 10
REG_R9_USR = 11
REG_R10_USR = 12
REG_R11_USR = 13
REG_R12_USR = 14
REG_R13_USR = 15
REG_R14_USR = 1615
REG_SPSR_FIQ = 17
REG_R8_FIQ = 18
REG_R9_FIQ = 19
REG_R10_FIQ = 20
REG_R11_FIQ = 21
REG_R12_FIQ = 22
REG_R13_FIQ = 23
REG_R14_FIQ = 24
REG_SPSR_SVC = 25
REG_R13_SVC = 26
REG_R14_SVC = 27
REG_SPSR_ABT = 28
REG_R13_ABT = 29
REG_R14_ABT = 30
REG_SPSR_IRQ = 31
REG_R13_IRQ = 32
REG_R14_IRQ = 33
REG_SPSR_UND = 34
REG_R13_UND = 35
REG_R14_UND = 36
REG_FPSID = 37
REG_FPSCR = 38
REG_FPEXC = 39
REG_FPS0 = 40
REG_FPS1 = 41
REG_FPS2 = 42
REG_FPS3 = 43
REG_FPS4 = 44
REG_FPS5 = 45
REG_FPS6 = 46
REG_FPS7 = 47
REG_FPS8 = 48
REG_FPS9 = 49
REG_FPS10 = 50
REG_FPS11 = 51
REG_FPS12 = 52
REG_FPS13 = 53
REG_FPS14 = 54
REG_FPS15 = 55
REG_FPS16 = 56
REG_FPS17 = 57
REG_FPS18 = 58
REG_FPS19 = 59
REG_FPS20 = 60
REG_FPS21 = 61
REG_FPS22 = 62
REG_FPS23 = 63
REG_FPS24 = 64
REG_FPS25 = 65
REG_FPS26 = 66
REG_FPS27 = 67
REG_FPS28 = 68
REG_FPS29 = 69
REG_FPS30 = 70
REG_FPS31 = 71
REG_MVFR0 = 72
REG_MVFR1 = 73

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

  def __init__(self, usb_number, device, itf):
    timeout = 10
    retried = False
    t0 = time.time()
    elapsed = -1
    while time.time() < t0 + timeout:
      self.jl, self.jlink_lib_name = get_jlink_dll()
      try:
        self._init(usb_number, device, itf)
        if retried:
          print 'success'
        return
      except JLinkException, x:
        if x.args[0] == -258:
          new_elapsed = int(time.time() - t0)
          if new_elapsed != elapsed:
            elapsed = new_elapsed
            print timeout - elapsed,
            sys.stdout.flush()
          retried = True
          continue
        else:
          raise
    else:
      raise

  def cmd_jlink(self, ui, args):
    """display jlink information"""
    ui.put('%s\n' % self)

  def __str__(self):
    s = []
    s.append('jlink library v%d %s' % (self.get_dll_version(), self.get_compile_data_time()))
    s.append('jlink device v%d sn%d %s' % (self.get_hw_version(), self.get_sn(), self.get_fw_string()))
    s.append('target voltage %.3fV' % (float(self.get_hw_status()['vref']) / 1000.0))
    return '\n'.join(s)

  def _init(self, usb_number, device, itf):
    self.select_usb(usb_number)
    self.jlink_open()
    state = self.get_hw_status()
    assert state['vref'] > 1500, 'Vref is too low. Check target power.'
    assert state['srst'] == 1, '~SRST signal is asserted. Target is held in reset.'
    self.exec_command('device=%s' % cpu_names[device])
    self.set_speed(4000)
    self.tif_select(itf)
    self.jlink_connect()

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
    return fn(ctypes.c_int(reg))

  def rd_pc(self):
    return self.rdreg(REG_R15_PC)

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

  def rd32(self, adr):
    return self.rdmem32(adr, 1)[0]

  def rd16(self, adr):
    return self.rdmem16(adr, 1)[0]

  def rd8(self, adr):
    return self.rdmem8(adr, 1)[0]

  # Note1: I'm not sure what the underlying store is for JLINKARM_WriteMem.
  # It stores an arbitrary number of bytes without overwriting adjacent memory locations,
  # but does it do 32 bit stores when it can? I'm not sure. If you want to ensure 8/16/32
  # stores then the JLINKARM_WriteU8/16/32 calls might be a better bet. But I'm not sure
  # how they work either.

  # Note2: I use JLINKARM_WriteMem for writing nand page data to the controller cache.
  # It works and is much faster than doing individual calls to JLINKARM_WriteU32.

  def wrmem32(self, adr, buf):
    """write a buffer of 32 bit values to a memory region"""
    # void JLINKARM_WriteMem(U32 addr, U32 count, const void * p);
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

# ----------------------------------------------------------------------------
