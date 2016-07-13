#------------------------------------------------------------------------------
"""

Serial Wire Debug

"""
#------------------------------------------------------------------------------

from bits import *

#------------------------------------------------------------------------------
# pre-canned swd sequences

# 50 SWCLK cycles with SWDIO driven high
_reset = bits()
_reset.ones(50)

# line reset: at least 50 SWCLK cycles with SWDIO driven high,
# followed by at least one idle (low) cycle
line_reset = _reset.copy()
line_reset.append(bits(1,(0,)))

# JTAG-to-SWD: at least 50 TCK/SWCLK cycles with TMS/SWDIO
# high, putting either interface logic into reset state, followed by a
# specific 16-bit sequence and finally a line reset in case the SWJ-DP was
# already in SWD mode.
jtag2swd = _reset.copy()
jtag2swd.append(bits(16,(0x9e,0xe7)))
jtag2swd.append(_reset)
jtag2swd.append(bits(2,(0,)))

# SWD-to-JTAG: at least 50 TCK/SWCLK cycles with TMS/SWDIO
# high, putting either interface logic into reset state, followed by a
# specific 16-bit sequence and finally at least 5 TCK cycles to put the
# JTAG TAP in TLR.
swd2jtag = _reset.copy()
swd2jtag.append(bits(16,(0x3c,0xe7)))
swd2jtag.append(bits(5,(0xff,)))

# SWD-to-dormant sequence: at least 50 SWCLK cycles with SWDIO high to
# put the interface in reset state, followed by a specific 16-bit sequence.
swd2dormant = _reset.copy()
swd2dormant.append(bits(16,(0xbc,0xe3)))

# Dormant-to-SWD sequence: at least 8 TCK/SWCLK cycles with TMS/SWDIO high
# to abort any ongoing selection alert sequence, followed by a specific 128-bit
# selection alert sequence, followed by 4 TCK/SWCLK cycles with TMS/SWDIO low,
# followed by a specific protocol-dependent activation code. For SWD the activation
# code is an 8-bit sequence. The sequence ends with a line reset.
dormant2swd = bits(8,(0xff,))
dormant2swd.append(bits(128,(0x92,0xf3,0x09,0x62,0x95,0x2d,0x85,0x86,0xe9,0xaf,0xdd,0xe3,0xa2,0x0e,0xbc,0x19)))
dormant2swd.append(bits(4,(0,)))
dormant2swd.append(bits(8,(0xa1,)))
dormant2swd.append(_reset)
dormant2swd.append(bits(1,(0,)))

#------------------------------------------------------------------------------
