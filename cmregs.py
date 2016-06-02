# -----------------------------------------------------------------------------
"""

Cortex-M Registers

The SVD files typically don't contain the core system periperhals defined for
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

def _build_registers(reg_info):
  registers = {}
  for (name, offset, descr) in reg_info:
    r = soc.register()
    r.name = name
    r.description = descr
    r.size = 32
    r.offset = offset
    r.fields = None
    registers[r.name] = r
  return registers

# -----------------------------------------------------------------------------
#  Nested Vectored Interrupt Controller

# base_name, offset, number, description
_cm0_nvic_info = (
  ('ISER', 0x000, 1, '(R/W) Interrupt Set Enable Register'),
  ('ICER', 0x080, 1, '(R/W) Interrupt Clear Enable Register'),
  ('ISPR', 0x100, 1, '(R/W) Interrupt Set Pending Register'),
  ('ICPR', 0x180, 1, '(R/W) Interrupt Clear Pending Register'),
  ('IABR', 0x200, 1, '(R/W) Interrupt Active Bit Register'),
  ('IPR', 0x300, 8, '(R/W) Interrupt Priority Register'),
)

_cm3_nvic_info = (
  ('ISER', 0x000, 8, '(R/W) Interrupt Set Enable Register'),
  ('ICER', 0x080, 8, '(R/W) Interrupt Clear Enable Register'),
  ('ISPR', 0x100, 8, '(R/W) Interrupt Set Pending Register'),
  ('ICPR', 0x180, 8, '(R/W) Interrupt Clear Pending Register'),
  ('IABR', 0x200, 8, '(R/W) Interrupt Active Bit Register'),
  ('IPR', 0x300, 60, '(R/W) Interrupt Priority Register'),
)

def _build_nvic_registers(nvic_info):
  registers = {}
  for (name, offset, n, descr) in nvic_info:
    for i in range(n):
      r = soc.register()
      r.name = '%s%d' % (name, i)
      r.description = '%s %d' % (descr, i)
      r.size = 32
      r.offset = offset + (i * 4)
      r.fields = None
      registers[r.name] = r
  return registers

def _build_nvic_peripheral(nvic_info):
  p = soc.peripheral()
  p.name = 'NVIC'
  p.description = 'Nested Vectored Interrupt Controller'
  p.address = NVIC_BASE
  p.size = None
  p.default_register_size = 32
  p.registers = _build_nvic_registers(nvic_info)
  return p

cm0_nvic = _build_nvic_peripheral(_cm0_nvic_info)
cm3_nvic = _build_nvic_peripheral(_cm3_nvic_info)

# -----------------------------------------------------------------------------
# SysTick

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
_p.registers = _build_registers(_systick_info)
systick = _p

# -----------------------------------------------------------------------------
# System Control Block

# name, offset, description
_cm0_scb_info = (
  ('CPUID', 0x000, '(R/ ) CPUID Base Register'),
  ('ICSR', 0x004, '(R/W) Interrupt Control and State Register'),
  ('VTOR', 0x008, '(R/W) Vector Table Offset Register'),
  ('AIRCR', 0x00C, '(R/W) Application Interrupt and Reset Control Register'),
  ('SCR', 0x010, '(R/W) System Control Register'),
  ('CCR', 0x014, '(R/W) Configuration Control Register'),
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
  p.registers = _build_registers(info)
  return p

cm0_scb = _build_scb_peripheral(_cm0_scb_info)
cm3_scb = _build_scb_peripheral(_cm3_scb_info)

# -----------------------------------------------------------------------------
# Memory Protection Unit





# -----------------------------------------------------------------------------
# Floating Point Unit




# -----------------------------------------------------------------------------
