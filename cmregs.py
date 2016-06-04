# -----------------------------------------------------------------------------
"""

Cortex-M Registers

The SVD files typically don't contain the core system peripherals defined for
the Cortex-M CPUs. Some vendors will define system peripherals with SoC
variablility (E.g. NVIC), but in general a device structure derived from an
SVD file will need to be appended with the system peripherals.

We define the system peripherals here and then selectively add them to
the device structure as part of the SoC fixup process.

Typically:
cm0* is for cm0 and cm0plus
cm3* is for cm3 and cm4

There are some minor register differences, and I'm not being overly precise.
We reference the registers by name, so it's more important to have the
right names in the right place so we can use common code to do system oriented
things.

Register and peripheral names are taken from the ARM documentation.

"""
# -----------------------------------------------------------------------------

import soc

# -----------------------------------------------------------------------------
# Memory mapping of Cortex-Mx Hardware

SCS_BASE = 0xE000E000 # System Control Space Base Address
ITM_BASE = 0xE0000000 # ITM Base Address
DWT_BASE = 0xE0001000 # DWT Base Address
TPI_BASE = 0xE0040000 # TPI Base Address
CoreDebug_BASE = 0xE000EDF0 # Core Debug Base Address
SysTick_BASE = (SCS_BASE + 0x0010) # SysTick Base Address
NVIC_BASE = (SCS_BASE + 0x0100) # NVIC Base Address
SCB_BASE = (SCS_BASE + 0x0D00) # System Control Block Base Address
MPU_BASE = (SCS_BASE + 0x0D90) # Memory Protection Unit Base Address
FPU_BASE = (SCS_BASE + 0x0F30) # Floating Point Unit Base Address

# -----------------------------------------------------------------------------

def _build_registers(p, reg_info):
  registers = {}
  for (name, offset, descr) in reg_info:
    r = soc.register()
    r.name = name
    r.description = descr
    r.size = 32
    r.offset = offset
    r.fields = None
    r.parent = p
    registers[r.name] = r
  return registers

# -----------------------------------------------------------------------------
#  Nested Vectored Interrupt Controller

def _build_nvic_registers(p, nvic_info):
  registers = {}
  for (name, offset, n, descr) in nvic_info:
    if n is None:
      # single instance of the register
      r = soc.register()
      r.name = name
      r.description = descr
      r.size = 32
      r.offset = offset
      r.fields = None
      r.parent = p
      registers[r.name] = r
    else:
      # multiple registers 0..n-1
      for i in range(n):
        r = soc.register()
        r.name = '%s%d' % (name, i)
        r.description = '%s %d' % (descr, i)
        r.size = 32
        r.offset = offset + (i * 4)
        r.fields = None
        r.parent = p
        registers[r.name] = r
  return registers

def build_nvic(n_ext):
  """build an nvic peripheral with n external interrupts"""

  # IPR registers support 4 interrupts per word.
  n_ipr = (n_ext + 3) >> 2
  # Other registers support 1 interrupt per bit
  n_other = (n_ext + 31) >> 5

  nvic_info = (
    ('ICTR', 0x004, None, '(R/ ) Interrupt Controller Type Register'),
    ('ISER', 0x100, n_other, '(R/W) Interrupt Set Enable Register'),
    ('ICER', 0x180, n_other, '(R/W) Interrupt Clear Enable Register'),
    ('ISPR', 0x200, n_other, '(R/W) Interrupt Set Pending Register'),
    ('ICPR', 0x280, n_other, '(R/W) Interrupt Clear Pending Register'),
    ('IABR', 0x300, n_other, '(R/W) Interrupt Active Bit Register'),
    ('IPR', 0x400, n_ipr, '(R/W) Interrupt Priority Register'),
  )

  p = soc.peripheral()
  p.name = 'NVIC'
  p.description = 'Nested Vectored Interrupt Controller'
  p.address = SCS_BASE
  p.size = None
  p.default_register_size = 32
  p.registers = _build_nvic_registers(p, nvic_info)
  return p

# -----------------------------------------------------------------------------
# SysTick

"""
def CLKSOURCE_format(x):
  return '(%d) %s' % (x, ('cpuclk', 'extclk')[x == 0])

f = []
f.append(fld('COUNTFLAG', 16, 16))
f.append(fld('CLKSOURCE', 2, 2, CLKSOURCE_format))
f.append(fld('TICKINT', 1, 1))
f.append(fld('ENABLE', 0, 0))
SysTick_CTRL_fields = fldset('SysTick_CTRL', f)

def TENMS_format(x):
  return ('0', '(0x%06x) %.2f MHz' % (x, float(x)/1e+4))[x != 0]

f = []
f.append(fld('NOREF', 31, 31))
f.append(fld('SKEW', 30, 30))
f.append(fld('TENMS', 23, 0, TENMS_format))
SysTick_CALIB_fields = fldset('SysTick_CALIB', f)
"""

# systick is a 24-bit down counter
SysTick_MAXCOUNT = (1 << 24) - 1

# name, offset, description
_systick_info = (
  ('CTRL', 0x00, '(R/W) SysTick Control and Status Register'),
  ('LOAD', 0x04, '(R/W) SysTick Reload Value Register'),
  ('VAL', 0x08, '(R/W) SysTick Current Value Register'),
  ('CALIB', 0x0c, '(R/ ) SysTick Calibration Register'),
)

_p = soc.peripheral()
_p.name = 'SysTick'
_p.description = 'SysTick'
_p.address = SysTick_BASE
_p.size = None
_p.default_register_size = 32
_p.registers = _build_registers(_p, _systick_info)
systick = _p

# -----------------------------------------------------------------------------
# System Control Block

# ACTLR?

"""
def Implementor_format(x):
  names = {
    0x41: 'ARM',
  }
  return '(0x%02x) %s' % (x, names.get(x, '?'))

def Part_Number_format(x):
  names = {
    0xc60: 'cortex-m0+',
    0xc20: 'cortex-m0',
    0xc21: 'cortex-m1',
    0xc23: 'cortex-m3',
    0xc24: 'cortex-m4',
    0xc27: 'cortex-m7',
  }
  return '(0x%03x) %s' % (x, names.get(x, '?'))

f = []
f.append(fld('Implementor', 31, 24, Implementor_format))
f.append(fld('Variant', 23, 20))
f.append(fld('Architecture', 19, 16))
f.append(fld('Part Number', 15, 4, Part_Number_format))
f.append(fld('Revision', 3, 0))
CPUID_fields = fldset('CPUID', f)
"""

# name, offset, description
_cm0_scb_info = (
  ('CPUID', 0x000, '(R/ ) CPUID Base Register'),
  ('ICSR', 0x004, '(R/W) Interrupt Control and State Register'),
  ('VTOR', 0x008, '(R/W) Vector Table Offset Register'),
  ('AIRCR', 0x00C, '(R/W) Application Interrupt and Reset Control Register'),
  ('SCR', 0x010, '(R/W) System Control Register'),
  ('CCR', 0x014, '(R/W) Configuration Control Register'),
  ('SHPR1', 0x018, '(R/W) System Handlers Priority Registers'), # not implemented on cm0
  ('SHPR2', 0x01c, '(R/W) System Handlers Priority Registers'),
  ('SHPR3', 0x020, '(R/W) System Handlers Priority Registers'),
  ('SHCSR', 0x024, '(R/W) System Handler Control and State Register'),
)

_cm3_scb_info = (
  ('CPUID', 0x000, '(R/ ) CPUID Base Register'),
  ('ICSR', 0x004, '(R/W) Interrupt Control and State Register'),
  ('VTOR', 0x008, '(R/W) Vector Table Offset Register'),
  ('AIRCR', 0x00C, '(R/W) Application Interrupt and Reset Control Register'),
  ('SCR', 0x010, '(R/W) System Control Register'),
  ('CCR', 0x014, '(R/W) Configuration Control Register'),
  ('SHPR1', 0x018, '(R/W) System Handlers Priority Registers'),
  ('SHPR2', 0x01c, '(R/W) System Handlers Priority Registers'),
  ('SHPR3', 0x020, '(R/W) System Handlers Priority Registers'),
  ('SHCSR', 0x024, '(R/W) System Handler Control and State Register'),
  ('CFSR', 0x028, '(R/W) Configurable Fault Status Register'),
  ('HFSR', 0x02C, '(R/W) HardFault Status Register'),
  ('DFSR', 0x030, '(R/W) Debug Fault Status Register'),
  ('MMFAR', 0x034, '(R/W) MemManage Fault Address Register'),
  ('BFAR', 0x038, '(R/W) BusFault Address Register'),
  ('AFSR', 0x03C, '(R/W) Auxiliary Fault Status Register'),
  ('ID_PFR0', 0x040, '(R/ ) Processor Feature Register'),
  ('ID_PFR1', 0x044, '(R/ ) Processor Feature Register'),
  ('ID_DFR0', 0x048, '(R/ ) Debug Feature Register'),
  ('ID_ADR0', 0x04C, '(R/ ) Auxiliary Feature Register'),
  ('ID_MMFR0', 0x050, '(R/ ) Memory Model Feature Register'),
  ('ID_MMFR1', 0x054, '(R/ ) Memory Model Feature Register'),
  ('ID_MMFR2', 0x058, '(R/ ) Memory Model Feature Register'),
  ('ID_MMFR3', 0x05c, '(R/ ) Memory Model Feature Register'),
  ('ID_ISAR0', 0x060, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR1', 0x064, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR2', 0x068, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR3', 0x06c, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR4', 0x070, '(R/ ) Instruction Set Attributes Register'),
  ('CPACR', 0x088, '(R/W) Coprocessor Access Control Register'),
  ('STIR', 0x200, '( /W) Software Trigger Interrupt Register'),
)

def _build_scb_peripheral(info):
  p = soc.peripheral()
  p.name = 'SCB'
  p.description = 'System Control Block'
  p.address = SCB_BASE
  p.size = None
  p.default_register_size = 32
  p.registers = _build_registers(p, info)
  return p

cm0_scb = _build_scb_peripheral(_cm0_scb_info)
cm3_scb = _build_scb_peripheral(_cm3_scb_info)

# -----------------------------------------------------------------------------
# Memory Protection Unit

_cm3_mpu_info = (
  ('TYPE', 0x00, '(R/ ) MPU Type Register'),
  ('CTRL', 0x04, '(R/W) MPU Control Register'),
  ('RNR', 0x08, '(R/W) MPU Region RNRber Register'),
  ('RBAR', 0x0C, '(R/W) MPU Region Base Address Register'),
  ('RASR', 0x10, '(R/W) MPU Region Attribute and Size Register'),
  ('RBAR_A1', 0x14, '(R/W) MPU Alias 1 Region Base Address Register'),
  ('RASR_A1', 0x18, '(R/W) MPU Alias 1 Region Attribute and Size Register'),
  ('RBAR_A2', 0x1C, '(R/W) MPU Alias 2 Region Base Address Register'),
  ('RASR_A2', 0x20, '(R/W) MPU Alias 2 Region Attribute and Size Register'),
  ('RBAR_A3', 0x24, '(R/W) MPU Alias 3 Region Base Address Register'),
  ('RASR_A3', 0x28, '(R/W) MPU Alias 3 Region Attribute and Size Register'),
)

_cm0_mpu_info = (
  ('TYPE', 0x00, '(R/ ) MPU Type Register'),
  ('CTRL', 0x04, '(R/W) MPU Control Register'),
  ('RNR', 0x08, '(R/W) MPU Region RNRber Register'),
  ('RBAR', 0x0C, '(R/W) MPU Region Base Address Register'),
  ('RASR', 0x10, '(R/W) MPU Region Attribute and Size Register'),
)

def _build_mpu_peripheral(info):
  p = soc.peripheral()
  p.name = 'MPU'
  p.description = 'Memory Protection Unit'
  p.address = MPU_BASE
  p.size = None
  p.default_register_size = 32
  p.registers = _build_registers(p, info)
  return p

cm0_mpu = _build_mpu_peripheral(_cm0_mpu_info)
cm3_mpu = _build_mpu_peripheral(_cm3_mpu_info)

# -----------------------------------------------------------------------------
# Floating Point Unit

_cm4_fpu_info = (
  ('FPCCR', 0x04, '(R/W) Floating-Point Context Control Register'),
  ('FPCAR', 0x08, '(R/W) Floating-Point Context Address Register'),
  ('FPDSCR', 0x0C, '(R/W) Floating-Point Default Status Control Register'),
  ('MVFR0', 0x10, '(R/ ) Media and FP Feature Register 0'),
  ('MVFR1', 0x14, '(R/ ) Media and FP Feature Register 1'),
)

_p = soc.peripheral()
_p.name = 'FPU'
_p.description = 'Floating Point Unit'
_p.address = FPU_BASE
_p.size = None
_p.default_register_size = 32
_p.registers = _build_registers(_p, _cm4_fpu_info)
cm4_fpu = _p

# -----------------------------------------------------------------------------
# Instrumentation Trace Macrocell Unit

# -----------------------------------------------------------------------------
# Flash Patch and Breakpoint Unit

# -----------------------------------------------------------------------------
# Data Watchpoint and Trace Unit

# -----------------------------------------------------------------------------
# Trace Port Interface Unit

# -----------------------------------------------------------------------------
