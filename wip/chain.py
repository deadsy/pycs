#-----------------------------------------------------------------------------
"""

JTAG Chain Specifications

"""
#-----------------------------------------------------------------------------
"""

BCM49408 JTAG Layout

There are 4 devices on the JTAG chain:

idx 0 bcm49408.arm0 irlen 4 idcode 0x5ba00477 mfg 0x23b (ARM Ltd.) part 0xba00 ver 0x5
idx 1 bcm49408.arm1 irlen 4 idcode 0x4ba00477 mfg 0x23b (ARM Ltd.) part 0xba00 ver 0x4
idx 2 bcm49408.dev2 irlen 5 idcode 0x0490817f mfg 0x0bf (Broadcom) part 0x4908 ver 0x0
idx 3 bcm49408.dev3 irlen 5 idcode 0x0490817f mfg 0x0bf (Broadcom) part 0x4908 ver 0x0

device 0 (ARM Core):

ir 8 drlen 35 # abort
ir 10 drlen 35 # dpacc
ir 11 drlen 35 # apacc
ir 14 drlen 32 # idcode
ir 15 drlen 1 # bypass
(other ir values have drlen == 1)

device 0 has APs:
ap 0: idr 0x44770002 rev 4 jedec 4:3b (ARM) class 8 (MEM-AP) ap 0:2 (APB) (supports 32 bit transfers)

This APB MEM-AP has the following components:

Core 0:
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb100 Cortex-A53 Debug Unit
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9a8 Cortex-A53 CTI (Cross Trigger)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9d3 Cortex-A53 PMU (Performance Monitor Unit)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb95d Cortex-A53 ETM (Embedded Trace)

Core 1:
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb100 Cortex-A53 Debug Unit
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9a8 Cortex-A53 CTI (Cross Trigger)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9d3 Cortex-A53 PMU (Performance Monitor Unit)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb95d Cortex-A53 ETM (Embedded Trace)

Core 2:
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb100 Cortex-A53 Debug Unit
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9a8 Cortex-A53 CTI (Cross Trigger)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9d3 Cortex-A53 PMU (Performance Monitor Unit)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb95d Cortex-A53 ETM (Embedded Trace)

Core 3:
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb100 Cortex-A53 Debug Unit
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9a8 Cortex-A53 CTI (Cross Trigger)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb9d3 Cortex-A53 PMU (Performance Monitor Unit)
INFO:adiv5:mem-ap 0:0 pidr 00000004000bb95d Cortex-A53 ETM (Embedded Trace)

Other:
INFO:adiv5:mem-ap 0:0 pidr 00000004002bb908 CSTF (Trace Funnel)
INFO:adiv5:mem-ap 0:0 pidr 00000004004bb912 TPIU (Trace Port Interface Unit)

device 1 (ARM Core):

ir 8 drlen 35 # abort
ir 10 drlen 35 # dpacc
ir 11 drlen 35 # apacc
ir 14 drlen 32 # idcode
ir 15 drlen 1 # bypass

device 1 has APs:
ap 0: idr 0x44770001 rev 4 jedec 4:3b (ARM) class 8 (MEM-AP) ap 0:1 (AHB) (supports 8/16/32/64 bit transfers)
ap 1: idr 0x24770002 rev 2 jedec 4:3b (ARM) class 8 (MEM-AP) ap 0:2 (APB) (supports 32 bit transfers)
ap 2: idr 0x14760010 rev 1 jedec 4:3b (ARM) class 0 (NONE) ap 1:0 (JTAG)

Note 1: ap 3-ff read (sometimes) as JTAG APs. Bad mojo happens when you try to read the IDRs of these APs
(The USB gets stuck). I don't think they are for real.

Note 2: There doesn't appear to be any debug peripherals on this device.

device 2 (mystery):

ir 1 drlen 32 # idcode
ir 3 drlen 32 # ?
ir 8 drlen 32 # ?
ir 9 drlen 32 # ?
ir 10 drlen 32 # ?
ir 11 drlen 96 # ?
ir 14 drlen 33 # ?
ir 31 drlen 1 # bypass
(other ir values have drlen == 1)

device 3 (mystery):

ir 0 can't read drlen
ir 1 can't read drlen
ir 2 can't read drlen
ir 3 drlen 4
ir 4 can't read drlen
ir 5 can't read drlen
ir 6 drlen 32
ir 7 drlen 1
ir 8 drlen 40
ir 9 drlen 32
ir 10 drlen 4
ir 11 can't read drlen
ir 12 can't read drlen
ir 13 can't read drlen
ir 14 drlen 32
ir 15 drlen 1
ir 16 can't read drlen
ir 17 can't read drlen
ir 18 can't read drlen
ir 19 can't read drlen
ir 20 can't read drlen
ir 21 can't read drlen
ir 22 drlen 32
ir 23 drlen 1
ir 24 can't read drlen
ir 25 can't read drlen
ir 26 can't read drlen
ir 27 can't read drlen
ir 28 can't read drlen
ir 29 can't read drlen
ir 30 drlen 32 # idcode
ir 31 drlen 1 # bypass

"""

bcm49408 = (
  # irlen, idcode, name
  (4, 0x5ba00477, 'bcm49408.arm0'), # ARM core
  (4, 0x4ba00477, 'bcm49408.arm1'), # ARM core
  (5, 0x0490817f, 'bcm49408.dev2'), # some broadcom device
  (5, 0x0490817f, 'bcm49408.dev3'), # some broadcom device
)

#-----------------------------------------------------------------------------
"""

BCM58625 JTAG Layout

idx 0 bcm58625.arm0 irlen 4 idcode 0x4ba00477 mfg 0x23b (ARM Ltd.) part 0xba00 ver 0x4

device 0 (ARM Core):

ir 8 drlen 35 # abort
ir 10 drlen 35 # dpacc
ir 11 drlen 35 # apacc
ir 14 drlen 32 # idcode
ir 15 drlen 1 # bypass
(other ir values have drlen == 1)

device 0 has APs:
ap 1: idr 0x24770002 rev 2 jedec 4:3b (ARM) class 8 (MEM-AP) ap 0:2 (APB)

"""

bcm58625 = (
  # irlen, idcode, name
  (4, 0x4ba00477, 'bcm58625.arm0'), # ARM core
)

#-----------------------------------------------------------------------------
