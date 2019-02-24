#-----------------------------------------------------------------------------
"""

ADIv5 MEM-AP and JTAG-AP Operations

"""
#-----------------------------------------------------------------------------

import logging
import util
import cortex_a53

log = logging.getLogger(__name__)

#-----------------------------------------------------------------------------
# Access Port Register Access (APACC)

APACC_CSW = 0x00 # control status word
APACC_TAR = 0x04 # transfer address register
APACC_DRW = 0x0c # data read/write
APACC_BD0 = 0x10 # banked data 0
APACC_BD1 = 0x14 # banked data 1
APACC_BD2 = 0x18 # banked data 2
APACC_BD3 = 0x1c # banked data 3
APACC_CFG = 0xf4 # configuration
APACC_BASE = 0xf8 # debug base address
APACC_IDR = 0xfc #identification

apacc_name = {
  APACC_CSW: 'csw',
  APACC_TAR: 'tar',
  APACC_DRW: 'drw',
  APACC_BD0: 'bd0',
  APACC_BD1: 'bd1',
  APACC_BD2: 'bd2',
  APACC_BD3: 'bd3',
  APACC_CFG: 'cfg',
  APACC_BASE: 'base',
  APACC_IDR: 'idr',
}

# RnW[0]
AP_WR = 0
AP_RD = 1

#-----------------------------------------------------------------------------
# Identification Register(IDR)

AP_CLASS_NONE = 0
AP_CLASS_MEM_AP = 8

AP_TYPE_JTAG = 0
AP_TYPE_AHB = 1
AP_TYPE_APB = 2
AP_TYPE_AXI = 4

def idr_decode(idr):
  """return a string for the IDR decode"""
  rev = util.bits(idr, (31, 28))
  jedec_cont = util.bits(idr, (27, 24))
  jedec_id = util.bits(idr, (23, 17))
  ap_class = util.bits(idr, (16, 13))
  ap_variant = util.bits(idr, (7, 4))
  ap_type = util.bits(idr, (3, 0))
  s = []
  if jedec_cont == 0x4 and jedec_id == 0x3b:
    jedec_name = 'ARM'
  else:
    jedec_name = '?'
  ap_name = {
    AP_TYPE_JTAG: 'JTAG',
    AP_TYPE_AHB: 'AHB',
    AP_TYPE_APB: 'APB',
    AP_TYPE_AXI: 'AXI',
  }
  class_name = {
    AP_CLASS_NONE: 'NONE',
    AP_CLASS_MEM_AP: 'MEM-AP',
  }
  s.append('idr 0x%08x' % idr)
  s.append('rev %x' % rev)
  s.append('jedec %x:%x (%s)' % (jedec_cont, jedec_id, jedec_name))
  s.append('class %x (%s)' % (ap_class, class_name.get(ap_class, '?')))
  s.append('ap %x:%x (%s)' % (ap_variant, ap_type, ap_name.get(ap_type, '?')))
  return ' '.join(s)

def is_mem_ap(idr):
  """return True if this IDR is for a MEM-AP"""
  ap_class = util.bits(idr, (16, 13))
  return ap_class == AP_CLASS_MEM_AP

def is_jtag_ap(idr):
  """return True if this IDR is for a JTAG-AP"""
  ap_class = util.bits(idr, (16, 13))
  ap_type = util.bits(idr, (3, 0))
  return ap_class == AP_CLASS_NONE and ap_type == AP_TYPE_JTAG

#-----------------------------------------------------------------------------
# MEM-AP Control/Status Word Register (CSW)

MEM_AP_CSW_8BIT = (0 << 0)
MEM_AP_CSW_16BIT = (1 << 0)
MEM_AP_CSW_32BIT = (2 << 0)
MEM_AP_CSW_64BIT = (3 << 0)
MEM_AP_CSW_128BIT = (4 << 0)
MEM_AP_CSW_256BIT = (5 << 0)
MEM_AP_CSW_SIZE_MASK = (7 << 0)

MEM_AP_CSW_ADDRINC_OFF = (0 << 4)
MEM_AP_CSW_ADDRINC_SINGLE = (1 << 4)
MEM_AP_CSW_ADDRINC_PACKED = (2 << 4)
MEM_AP_CSW_ADDRINC_MASK = (3 << 4)

MEM_AP_CSW_DEVICE_EN = (1 << 6)
MEM_AP_CSW_TRIN_PROG = (1 << 7)
MEM_AP_CSW_SPIDEN = (1 << 23)

MEM_AP_CSW_HPROT = (1 << 25) # ?
MEM_AP_CSW_MASTER_DEBUG = (1 << 29) # ?
MEM_AP_CSW_SPROT = (1 << 30)
MEM_AP_CSW_DBGSWENABLE = (1 << 31)

MEM_AP_CSW_Size = {
  8: MEM_AP_CSW_8BIT,
  16: MEM_AP_CSW_16BIT,
  32: MEM_AP_CSW_32BIT,
  64: MEM_AP_CSW_64BIT,
  128: MEM_AP_CSW_128BIT,
  256: MEM_AP_CSW_256BIT,
}

MEM_AP_CSW_Size_format = {
  MEM_AP_CSW_8BIT: '8 bit',
  MEM_AP_CSW_16BIT: '16 bit',
  MEM_AP_CSW_32BIT: '32 bit',
  MEM_AP_CSW_64BIT: '64 bit',
  MEM_AP_CSW_128BIT: '128 bit',
  MEM_AP_CSW_256BIT: '256 bit',
}

MEM_AP_CSW_AddrInc_format = {
  0: 'off',
  1: 'single',
  2: 'packed',
}

MEM_AP_CSW_fieldset = (
  ('Size', 2, 0, MEM_AP_CSW_Size_format, 'transfer size'),
  ('AddrInc', 5, 4, MEM_AP_CSW_AddrInc_format, 'address increment'),
  ('DeviceEn', 6, 6, None, 'device enable'),
  ('TrInProg', 7, 7, None, 'transfer in progress'),
  ('Mode', 11, 8, None, ''),
  ('Type', 15, 12, None, ''),
  ('SPIDEN', 23, 23, None, 'secure privileged debug enable'),
  ('Prot', 30, 24, None, 'bus access protection control'),
  ('DbgSwEnable', 31, 31, None, 'debug software enable'),
)

#-----------------------------------------------------------------------------
# Component ID Register (CIDR)

CIDR0_OFS = 0xFF0
CIDR1_OFS = 0xFF4
CIDR2_OFS = 0xFF8
CIDR3_OFS = 0xFFC

CIDR_PREAMBLE = 0xB105000D
CIDR_CLASS_MASK = 0x0000F000
CIDR_CLASS_SHIFT = 12

# component classes
CIDR_CLASS_GVC = 0x0
CIDR_CLASS_ROMTAB = 0x1 # romtable, see ADIv5.2 chapter 10
CIDR_CLASS_DC = 0x9 # debug component, see coresight architecture specification
CIDR_CLASS_PTB = 0xB
CIDR_CLASS_DESS = 0xD
CIDR_CLASS_GIPC = 0xE
CIDR_CLASS_PCP = 0xF
CIDR_CLASS_UNKNOWN = 0x10

CIDR_CLASS_Names = {
  CIDR_CLASS_GVC: 'generic verification component',
  CIDR_CLASS_ROMTAB: 'rom table',
  CIDR_CLASS_DC: 'debug component',
  CIDR_CLASS_PTB: 'peripheral test block',
  CIDR_CLASS_DESS: 'OptimoDE Data Engine SubSystem (DESS) component',
  CIDR_CLASS_GIPC: 'generic ip component',
  CIDR_CLASS_PCP: 'primecell peripheral',
  CIDR_CLASS_UNKNOWN: 'unknown component class',
}

#-----------------------------------------------------------------------------
# Peripheral ID Register (PIDR)

PIDR0_OFS = 0xFE0
PIDR1_OFS = 0xFE4
PIDR2_OFS = 0xFE8
PIDR3_OFS = 0xFEC
PIDR4_OFS = 0xFD0
PIDR5_OFS = 0xFD4
PIDR6_OFS = 0xFD8
PIDR7_OFS = 0xFDC

PIDR_REV_MASK = 0x0FFF00000 # Revision bits
PIDR_PN_MASK = 0x000000FFF # Part number bits
PIDR_ARM_BITS = 0x4000BB000 # These make up the ARM JEP-106 code

class peripheral(object):
  """MEM-AP peripheral"""
  def __init__(self, pn, probe, cidr_class, descr):
    self.pn = pn
    self.probe = probe
    self.cidr_class = cidr_class
    self.descr = descr

class peripheral_database(object):
  """database of known MEM-AP peripherals"""
  def __init__(self):
    self.db = {}
  def add(self, p):
    """add a peripheral to the database"""
    self.db[p.pn] = p
  def lookup(self, pn):
    """lookup a peripheral by part number"""
    return self.db.get(pn, None)

# Peripheral ID Database
peripheral_db = peripheral_database()
peripheral_db.add(peripheral(0x000, None, CIDR_CLASS_GIPC, 'Cortex-M3 SCS (System Control Space)'))
peripheral_db.add(peripheral(0x001, None, CIDR_CLASS_UNKNOWN, 'Cortex-M3 ITM (Instrumentation Trace Module)'))
peripheral_db.add(peripheral(0x002, None, CIDR_CLASS_UNKNOWN, 'Cortex-M3 DWT (Data Watchpoint and Trace)'))
peripheral_db.add(peripheral(0x003, None, CIDR_CLASS_UNKNOWN, 'Cortex-M3 FBP (Flash Patch and Breakpoint)'))
peripheral_db.add(peripheral(0x008, None, CIDR_CLASS_GIPC, 'Cortex-M0 SCS (System Control Space)'))
peripheral_db.add(peripheral(0x00a, None, CIDR_CLASS_UNKNOWN, 'Cortex-M0 DWT (Data Watchpoint and Trace)'))
peripheral_db.add(peripheral(0x00b, None, CIDR_CLASS_UNKNOWN, 'Cortex-M0 BPU (Breakpoint Unit)'))
peripheral_db.add(peripheral(0x00c, None, CIDR_CLASS_GIPC, 'Cortex-M4 SCS (System Control Space)'))
peripheral_db.add(peripheral(0x00d, None, CIDR_CLASS_UNKNOWN, ' ETM11 (Embedded Trace)'))
peripheral_db.add(peripheral(0x100, cortex_a53.debug, CIDR_CLASS_DC, 'Cortex-A53 Debug Unit')) # non ARM- The Broadcom B53 (bcm49408)
peripheral_db.add(peripheral(0x490, None, CIDR_CLASS_UNKNOWN, 'Cortex-A15 GIC (Generic Interrupt Controller)'))
peripheral_db.add(peripheral(0x4c7, None, CIDR_CLASS_UNKNOWN, 'Cortex-M7 PPB (Private Peripheral Bus ROM Table)'))
peripheral_db.add(peripheral(0x906, None, CIDR_CLASS_UNKNOWN, 'CTI (Cross Trigger)'))
peripheral_db.add(peripheral(0x907, None, CIDR_CLASS_UNKNOWN, 'ETB (Trace Buffer)'))
peripheral_db.add(peripheral(0x908, None, CIDR_CLASS_UNKNOWN, 'CSTF (Trace Funnel)'))
peripheral_db.add(peripheral(0x910, None, CIDR_CLASS_UNKNOWN, 'ETM9 (Embedded Trace)'))
peripheral_db.add(peripheral(0x912, None, CIDR_CLASS_UNKNOWN, 'TPIU (Trace Port Interface Unit)'))
peripheral_db.add(peripheral(0x913, None, CIDR_CLASS_UNKNOWN, 'ITM (Instrumentation Trace Macrocell)'))
peripheral_db.add(peripheral(0x914, None, CIDR_CLASS_UNKNOWN, 'SWO (Single Wire Output)'))
peripheral_db.add(peripheral(0x917, None, CIDR_CLASS_UNKNOWN, 'HTM (AHB Trace Macrocell)'))
peripheral_db.add(peripheral(0x920, None, CIDR_CLASS_UNKNOWN, 'ETM11 (Embedded Trace)'))
peripheral_db.add(peripheral(0x921, None, CIDR_CLASS_UNKNOWN, 'Cortex-A8 ETM (Embedded Trace)'))
peripheral_db.add(peripheral(0x922, None, CIDR_CLASS_UNKNOWN, 'Cortex-A8 CTI (Cross Trigger)'))
peripheral_db.add(peripheral(0x923, None, CIDR_CLASS_UNKNOWN, 'Cortex-M3 TPIU (Trace Port Interface Unit)'))
peripheral_db.add(peripheral(0x924, None, CIDR_CLASS_UNKNOWN, 'Cortex-M3 ETM (Embedded Trace)'))
peripheral_db.add(peripheral(0x925, None, CIDR_CLASS_UNKNOWN, 'Cortex-M4 ETM (Embedded Trace)'))
peripheral_db.add(peripheral(0x930, None, CIDR_CLASS_UNKNOWN, 'Cortex-R4 ETM (Embedded Trace)'))
peripheral_db.add(peripheral(0x941, None, CIDR_CLASS_UNKNOWN, 'TPIU-Lite (Trace Port Interface Unit)'))
peripheral_db.add(peripheral(0x950, None, CIDR_CLASS_UNKNOWN, 'Cortex-A9 (unidentified component)'))
peripheral_db.add(peripheral(0x955, None, CIDR_CLASS_UNKNOWN, 'Cortex-A5 (unidentifed component)'))
peripheral_db.add(peripheral(0x95d, cortex_a53.etm, CIDR_CLASS_DC, 'Cortex-A53 ETM (Embedded Trace)'))
peripheral_db.add(peripheral(0x95f, None, CIDR_CLASS_UNKNOWN, 'Cortex-A15 PTM (Program Trace Macrocell)'))
peripheral_db.add(peripheral(0x961, None, CIDR_CLASS_UNKNOWN, 'TMC (Trace Memory Controller)'))
peripheral_db.add(peripheral(0x962, None, CIDR_CLASS_UNKNOWN, 'STM (System Trace Macrocell)'))
peripheral_db.add(peripheral(0x9a0, None, CIDR_CLASS_UNKNOWN, 'PMU (Performance Monitoring Unit)'))
peripheral_db.add(peripheral(0x9a1, None, CIDR_CLASS_UNKNOWN, 'Cortex-M4 TPIU (Trace Port Interface Unit)'))
peripheral_db.add(peripheral(0x9a5, None, CIDR_CLASS_UNKNOWN, 'Cortex-A5 ETM (Embedded Trace)'))
peripheral_db.add(peripheral(0x9a7, None, CIDR_CLASS_UNKNOWN, 'Cortex-A7 PMU (Performance Monitor Unit)'))
peripheral_db.add(peripheral(0x9a8, cortex_a53.cti, CIDR_CLASS_DC, 'Cortex-A53 CTI (Cross Trigger)'))
peripheral_db.add(peripheral(0x9af, None, CIDR_CLASS_UNKNOWN, 'Cortex-A15 PMU (Performance Monitor Unit)'))
peripheral_db.add(peripheral(0x9d3, cortex_a53.pmu, CIDR_CLASS_DC, 'Cortex-A53 PMU (Performance Monitor Unit)'))
peripheral_db.add(peripheral(0xc05, None, CIDR_CLASS_DC, 'Cortex-A5 Debug Unit'))
peripheral_db.add(peripheral(0xc07, None, CIDR_CLASS_DC, 'Cortex-A7 Debug Unit'))
peripheral_db.add(peripheral(0xc08, None, CIDR_CLASS_DC, 'Cortex-A8 Debug Unit'))
peripheral_db.add(peripheral(0xc09, None, CIDR_CLASS_DC, 'Cortex-A9 Debug Unit'))
peripheral_db.add(peripheral(0xc0f, None, CIDR_CLASS_UNKNOWN, 'Cortex-A15 Debug Unit'))
peripheral_db.add(peripheral(0xc14, None, CIDR_CLASS_UNKNOWN, 'Cortex-R4 Debug Unit'))
peripheral_db.add(peripheral(0xd03, cortex_a53.debug, CIDR_CLASS_DC, 'Cortex-A53 Debug Unit'))

#{ ARM_ID, 0x00e, "Cortex-M7 FPB",              "(Flash Patch and Breakpoint)", },
#{ ARM_ID, 0x4a1, "Cortex-A53 ROM",             "(v8 Memory Map ROM Table)", },
#{ ARM_ID, 0x4a2, "Cortex-A57 ROM",             "(ROM Table)", },
#{ ARM_ID, 0x4a3, "Cortex-A53 ROM",             "(v7 Memory Map ROM Table)", },
#{ ARM_ID, 0x4a4, "Cortex-A72 ROM",             "(ROM Table)", },
#{ ARM_ID, 0x4af, "Cortex-A15 ROM",             "(ROM Table)", },
#{ ARM_ID, 0x4c0, "Cortex-M0+ ROM",             "(ROM Table)", },
#{ ARM_ID, 0x4c3, "Cortex-M3 ROM",              "(ROM Table)", },
#{ ARM_ID, 0x4c4, "Cortex-M4 ROM",              "(ROM Table)", },
#{ ARM_ID, 0x4c8, "Cortex-M7 ROM",              "(ROM Table)", },
#{ ARM_ID, 0x470, "Cortex-M1 ROM",              "(ROM Table)", },
#{ ARM_ID, 0x471, "Cortex-M0 ROM",              "(ROM Table)", },
#{ ARM_ID, 0x909, "CoreSight ATBR",             "(Advanced Trace Bus Replicator)", },
#{ ARM_ID, 0x931, "Cortex-R5 ETM",              "(Embedded Trace)", },
#{ ARM_ID, 0x932, "CoreSight MTB-M0+",          "(Micro Trace Buffer)", },
#{ ARM_ID, 0x95a, "Cortex-A72 ETM",             "(Embedded Trace)", },
#{ ARM_ID, 0x95b, "Cortex-A17 PTM",             "(Program Trace Macrocell)", },
#{ ARM_ID, 0x95e, "Cortex-A57 ETM",             "(Embedded Trace)", },
#{ ARM_ID, 0x975, "Cortex-M7 ETM",              "(Embedded Trace)", },
#{ ARM_ID, 0x9a4, "CoreSight GPR",              "(Granular Power Requester)", },
#{ ARM_ID, 0x9a9, "Cortex-M7 TPIU",             "(Trace Port Interface Unit)", },
#{ ARM_ID, 0x9ae, "Cortex-A17 PMU",             "(Performance Monitor Unit)", },
#{ ARM_ID, 0x9b7, "Cortex-R7 PMU",              "(Performance Monitoring Unit)", },
#{ ARM_ID, 0x9d7, "Cortex-A57 PMU",             "(Performance Monitor Unit)", },
#{ ARM_ID, 0x9d8, "Cortex-A72 PMU",             "(Performance Monitor Unit)", },
#{ ARM_ID, 0xc0e, "Cortex-A17 Debug",           "(Debug Unit)", },
#{ ARM_ID, 0xc15, "Cortex-R5 Debug",            "(Debug Unit)", },
#{ ARM_ID, 0xc17, "Cortex-R7 Debug",            "(Debug Unit)", },
#{ ARM_ID, 0xd07, "Cortex-A57 Debug",           "(Debug Unit)", },
#{ ARM_ID, 0xd08, "Cortex-A72 Debug",           "(Debug Unit)", },

#-----------------------------------------------------------------------------
# MEM-APs

def extract(val, adr, size):
  """extract data from data lane based on size and address"""
  if size == 8:
    return (val >> ((adr & 3) << 3)) & 0xff
  elif size == 16:
    return (val >> ((adr & 2) << 3)) & 0xffff
  elif size == 32:
    return val
  elif size == 64:
    assert False, "TODO: 64 bit extract"
  elif size == 128:
    assert False, "TODO: 128 bit extract"
  elif size == 256:
    assert False, "TODO: 256 bit extract"
  else:
    assert False, "bad extract size"

class mem_ap_error(IOError):
  """Error with MEM-MAP"""

class mem_ap(object):
  """MEM-AP object"""

  def __init__(self, dp, apnum, idr):
    self.dp = dp # debug port
    self.apnum = apnum # ap number
    self.idr = idr # cached idr value
    self.cfg = self.rd_apacc(APACC_CFG)
    self.base = self.rd_apacc(APACC_BASE)
    self.csw = self.rd_apacc(APACC_CSW) & ~(MEM_AP_CSW_SIZE_MASK | MEM_AP_CSW_ADDRINC_MASK)
    if self.csw & MEM_AP_CSW_TRIN_PROG:
      self.csw &= ~MEM_AP_CSW_TRIN_PROG
    log.info(str(self))
    if self.base == 0xffffffff:
      log.info('%s no debug entries present' % self.name())
    else:
      self.component_probe(self.base)

  def wr_apacc(self, adr, val):
    """write an APACC register"""
    self.dp.wr_apacc(self.apnum, adr, val)

  def rd_apacc(self, adr):
    """read an APACC register"""
    return self.dp.rd_apacc(self.apnum, adr)

  #def transfer_sizes(self):
    #"""return the list of transfer sizes supported by the AP"""
    #supported = []
    ## save current csw
    #saved_csw = self.rd_csw()
    #csw = saved_csw
    #for size in (8, 16, 32, 64, 128, 256):
      #x = MEM_AP_CSW_Size[size]
      #self.wr_csw((csw & ~MEM_AP_CSW_SIZE_MASK) | x)
      #if self.rd_csw() & MEM_AP_CSW_SIZE_MASK == x:
        #supported.append(size)
    ## restore csw
    #self.wr_csw(saved_csw)
    #return supported

  def mem_setup(self, adr, size):
    """Program the CSW and TAR for sequencial access at a given transfer size"""
    self.wr_apacc(APACC_CSW, self.csw | MEM_AP_CSW_ADDRINC_SINGLE | MEM_AP_CSW_Size[size])
    self.dp.rw_apacc(AP_WR, APACC_TAR, adr)

  def mem_rd(self, adr, n, size):
    """memory read, n x size bits"""
    assert adr & ((size >> 3) - 1) == 0, 'adr(%08x) is not on a size(%d) bits boundary' % (adr, size)
    rd = []
    oadr = adr
    self.mem_setup(adr, size)
    self.dp.rw_apacc(AP_RD, APACC_DRW, 0)
    for _ in range(n - 1):
      val = self.dp.rw_apacc(AP_RD, APACC_DRW, 0)
      rd.append(extract(val, adr, size))
      adr += (size >> 3)
      # Check for 10 bit address overflow
      if (adr ^ oadr) & 0xfffffc00:
        oadr = adr
        self.dp.rw_apacc(AP_WR, APACC_TAR, adr)
        self.dp.rw_apacc(AP_RD, APACC_DRW, 0)
    # read the last value
    val = self.dp.rd_rdbuff()
    rd.append(extract(val, adr, size))
    return rd

  def mem_rd32(self, adr):
    """memory read, 1 x 32 bits"""
    return self.mem_rd(adr, 1, 32)[0]

  def component_probe(self, adr):
    """probe the component at an address"""
    adr &= ~3

    # get the 64 bit peripheral ID register
    pidr = 0
    for ofs in (PIDR7_OFS, PIDR6_OFS, PIDR5_OFS, PIDR4_OFS, PIDR3_OFS, PIDR2_OFS, PIDR1_OFS, PIDR0_OFS):
      x = self.mem_rd32(adr + ofs)
      pidr = (pidr << 8) | (x & 0xff)
    # check for errors
    if self.dp.error() != 0:
      raise mem_ap_error('error reading PIDR for %08x' % adr)

    # get the 32 bit component ID register
    cidr = 0
    for ofs in (CIDR3_OFS, CIDR2_OFS, CIDR1_OFS, CIDR0_OFS):
      x = self.mem_rd32(adr + ofs)
      cidr = (cidr << 8) | (x & 0xff)
    # check for errors
    if self.dp.error() != 0:
      raise mem_ap_error('error reading CIDR for %08x' % adr)

    # check the CIDR preamble
    if cidr & ~CIDR_CLASS_MASK != CIDR_PREAMBLE:
      raise mem_ap_error('bad cidr %08x preamble at %08x' % (cidr, adr))
    # get the cidr class
    cidr_class = (cidr & CIDR_CLASS_MASK) >> CIDR_CLASS_SHIFT
    log.info('%s cidr %08x (%s)' % (self.name(), cidr, CIDR_CLASS_Names.get(cidr_class, '?')))

    if cidr_class == CIDR_CLASS_ROMTAB:
      # rom table - probe recursively
      ofs = 0
      while ofs < 0xf00:
        entry = self.mem_rd32(adr + ofs)
        if self.dp.error() != 0:
          raise mem_ap_error('error reading rom table entry 0x%08x' % (adr + ofs))
        ofs += 4
        if entry == 0:
          # end of rom table
          break
        if entry & 1 == 0:
          # entry not present
          continue
        # recursively probe the component
        self.component_probe(adr + (entry & 0xfffff000))
    else:
      # if the peripheral was not made by ARM we don't support it
      if pidr & ~(PIDR_REV_MASK | PIDR_PN_MASK) != PIDR_ARM_BITS:
        log.info('%s pidr %016x does not match ARM JEP-106' % (self.name(), pidr))
        return
      # lookup the peripheral by part number
      pn = pidr & PIDR_PN_MASK
      p = peripheral_db.lookup(pn)
      if p is not None:
        # known part number
        log.info('%s pidr %016x %s' % (self.name(), pidr, p.descr))
        # sanity check the component class
        if (p.cidr_class != CIDR_CLASS_UNKNOWN) and (cidr_class != p.cidr_class):
          log.info('component class mismatch: expected 0x%x read 0x%x' % (p.cidr_class, cidr_class))
        # call the probe function
        if p.probe is not None:
          x = p.probe(self, adr)
          log.info(str(x))
      else:
        # unknown part number
        log.info('%s pidr %016x unknown (%03x)' % (self.name(), pidr, pn))

  def name(self):
    return 'mem-ap %x:%x' % (self.dp.device.idx, self.apnum)

  def __str__(self):
    return '%s %s' % (self.name(), idr_decode(self.idr))

def probe_mem_ap(dp, n=256):
  """return a list of MEM-APs available on the debug port"""
  aps = []
  for apnum in range(n):
    idr = dp.rd_apacc(apnum, APACC_IDR)
    if idr != 0 and is_mem_ap(idr):
      x = mem_ap(dp, apnum, idr)
      aps.append(x)
  return aps

#-----------------------------------------------------------------------------
# JTAG-APs

class jtag_ap(object):
  """JTAG-AP object"""

  def __init__(self, dp, apnum, idr):
    self.dp = dp # debug port
    self.apnum = apnum # ap number
    self.idr = idr # cached idr value
    log.info(str(self))

  def __str__(self):
    return 'jtag-ap %x:%x: %s' % (self.dp.device.idx, self.apnum, idr_decode(self.idr))

def probe_jtag_ap(dp, n=256):
  """return a list of JTAG-APs available on the debug port"""
  aps = []
  for apnum in range(n):
    idr = dp.rd_apacc(apnum, APACC_IDR)
    if idr != 0 and is_jtag_ap(idr):
      x = jtag_ap(dp, apnum, idr)
      aps.append(x)
  return aps


#-----------------------------------------------------------------------------
