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
import cortexm

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
  p.size = 4 << 10
  p.default_register_size = 32
  p.registers = _build_nvic_registers(p, nvic_info)
  return p

# -----------------------------------------------------------------------------
# SysTick

# systick is a 24-bit down counter
SysTick_MAXCOUNT = (1 << 24) - 1

def _CLKSOURCE_format(x):
  return '%s' % ('cpuclk', 'extclk')[x == 0]

def _TENMS_format(x):
  return ('', '%.2f MHz' % (float(x)/1e+4))[x != 0]

_ctrl_fieldset = (
  ('COUNTFLAG', 16, 16, None, None),
  ('CLKSOURCE', 2, 2, _CLKSOURCE_format, None),
  ('TICKINT', 1, 1, None, None),
  ('ENABLE', 0, 0, None, None),
)

_calib_fieldset = (
  ('NOREF', 31, 31, None, None),
  ('SKEW', 30, 30, None, None),
  ('TENMS', 23, 0, _TENMS_format, None),
)

_systick_regset = (
  ('CTRL', 32, 0x00, _ctrl_fieldset, '(R/W) SysTick Control and Status Register'),
  ('LOAD', 32, 0x04, None, '(R/W) SysTick Reload Value Register'),
  ('VAL', 32, 0x08, None, '(R/W) SysTick Current Value Register'),
  ('CALIB', 32, 0x0c, _calib_fieldset, '(R/ ) SysTick Calibration Register'),
)

systick = soc.make_peripheral('SysTick', SysTick_BASE, 1 << 10, _systick_regset, 'SysTick')

# -----------------------------------------------------------------------------
# System Control Block

# ACTLR?

_implementor_enumset = (
  ('ARM', 0x41, None),
)

_part_number_enumset = (
  ('CM0+', 0xc60, None),
  ('CM0',  0xc20, None),
  ('CM1',  0xc21, None),
  ('CM3',  0xc23, None),
  ('CM4',  0xc24, None),
  ('CM7',  0xc27, None),
)

_cpuid_fieldset = (
  ('Implementor', 31, 24, _implementor_enumset, None),
  ('Variant', 23, 20, None, None),
  ('Architecture', 19, 16, None, None),
  ('Part Number', 15, 4, _part_number_enumset, None),
  ('Revision', 3, 0, None, None),
)

# name, offset, description
_cm0_scb_regset = (
  ('CPUID', 32, 0x000, _cpuid_fieldset, '(R/ ) CPUID Base Register'),
  ('ICSR', 32, 0x004, None, '(R/W) Interrupt Control and State Register'),
  ('VTOR', 32, 0x008, None, '(R/W) Vector Table Offset Register'),
  ('AIRCR', 32, 0x00C, None, '(R/W) Application Interrupt and Reset Control Register'),
  ('SCR', 32, 0x010, None, '(R/W) System Control Register'),
  ('CCR', 32, 0x014, None, '(R/W) Configuration Control Register'),
  ('SHPR1', 32, 0x018, None, '(R/W) System Handlers Priority Registers'), # not implemented on cm0
  ('SHPR2', 32, 0x01c, None, '(R/W) System Handlers Priority Registers'),
  ('SHPR3', 32, 0x020, None, '(R/W) System Handlers Priority Registers'),
  ('SHCSR', 32, 0x024, None, '(R/W) System Handler Control and State Register'),
)

_cm3_scb_regset = (
  ('CPUID', 32, 0x000, _cpuid_fieldset, '(R/ ) CPUID Base Register'),
  ('ICSR', 32, 0x004, None, '(R/W) Interrupt Control and State Register'),
  ('VTOR', 32, 0x008, None, '(R/W) Vector Table Offset Register'),
  ('AIRCR', 32, 0x00C, None, '(R/W) Application Interrupt and Reset Control Register'),
  ('SCR', 32, 0x010, None, '(R/W) System Control Register'),
  ('CCR', 32, 0x014, None, '(R/W) Configuration Control Register'),
  ('SHPR1', 32, 0x018, None, '(R/W) System Handlers Priority Registers'),
  ('SHPR2', 32, 0x01c, None, '(R/W) System Handlers Priority Registers'),
  ('SHPR3', 32, 0x020, None, '(R/W) System Handlers Priority Registers'),
  ('SHCSR', 32, 0x024, None, '(R/W) System Handler Control and State Register'),
  ('CFSR', 32, 0x028, None, '(R/W) Configurable Fault Status Register'),
  ('HFSR', 32, 0x02C, None, '(R/W) HardFault Status Register'),
  ('DFSR', 32, 0x030, None, '(R/W) Debug Fault Status Register'),
  ('MMFAR', 32,  0x034, None, '(R/W) MemManage Fault Address Register'),
  ('BFAR', 32, 0x038, None, '(R/W) BusFault Address Register'),
  ('AFSR', 32, 0x03C, None, '(R/W) Auxiliary Fault Status Register'),
  ('ID_PFR0', 32, 0x040, None, '(R/ ) Processor Feature Register'),
  ('ID_PFR1', 32, 0x044, None, '(R/ ) Processor Feature Register'),
  ('ID_DFR0', 32, 0x048, None, '(R/ ) Debug Feature Register'),
  ('ID_ADR0', 32, 0x04C, None, '(R/ ) Auxiliary Feature Register'),
  ('ID_MMFR0', 32, 0x050, None, '(R/ ) Memory Model Feature Register'),
  ('ID_MMFR1', 32, 0x054, None, '(R/ ) Memory Model Feature Register'),
  ('ID_MMFR2', 32, 0x058, None, '(R/ ) Memory Model Feature Register'),
  ('ID_MMFR3', 32, 0x05c, None, '(R/ ) Memory Model Feature Register'),
  ('ID_ISAR0', 32, 0x060, None, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR1', 32, 0x064, None, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR2', 32, 0x068, None, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR3', 32, 0x06c, None, '(R/ ) Instruction Set Attributes Register'),
  ('ID_ISAR4', 32, 0x070, None, '(R/ ) Instruction Set Attributes Register'),
  ('CPACR', 32, 0x088, None, '(R/W) Coprocessor Access Control Register'),
  ('STIR', 32, 0x200, None, '( /W) Software Trigger Interrupt Register'),
)

cm0_scb = soc.make_peripheral('SCB', SCB_BASE, 1 << 10, _cm0_scb_regset, 'System Control Block')
cm3_scb = soc.make_peripheral('SCB', SCB_BASE, 1 << 10, _cm3_scb_regset, 'System Control Block')

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
# CPU Fixup Functions

def cm0_fixup(d):
  d.cpu_info.name = 'CM0'
  d.cpu_info.nvicPrioBits = 2
  d.insert(systick)
  d.insert(cm0_scb)
  d.insert(build_nvic(d.cpu_info.deviceNumInterrupts))
  cortexm.add_system_exceptions(d)

def cm0plus_fixup(d):
  d.cpu_info.name = 'CM0+'
  d.cpu_info.nvicPrioBits = 2
  d.insert(systick)
  d.insert(cm0_scb)
  d.insert(build_nvic(d.cpu_info.deviceNumInterrupts))
  cortexm.add_system_exceptions(d)

def cm4_fixup(d):
  d.cpu_info.name = 'CM4'
  d.insert(systick)
  d.insert(cm3_scb)
  d.insert(build_nvic(d.cpu_info.deviceNumInterrupts))
  cortexm.add_system_exceptions(d)

# -----------------------------------------------------------------------------
