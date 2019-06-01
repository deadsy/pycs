# -----------------------------------------------------------------------------
"""

MIMXRT-1020-EVK Evaluation Kit (i.MX RT1020)


SoC: NXP PIMXRT1021DAG5A
SDRAM: ISSI IS42S16160J-6TLI
CODEC: Cirrus Logic WM8960G
Ethernet Phy: Microchip KSZ8081

"""
# -----------------------------------------------------------------------------

import cli
import cortexm
import mem
import soc
import vendor.nxp.imxrt as imxrt

# -----------------------------------------------------------------------------

soc_name = 'RT1020'
prompt = 'rt1020'

# -----------------------------------------------------------------------------
