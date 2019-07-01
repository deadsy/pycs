#-----------------------------------------------------------------------------
"""

SoC file for NXP i.MX RT devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequecies.

"""
#-----------------------------------------------------------------------------

import soc
import cmregs
import cortexm

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

#-----------------------------------------------------------------------------
# flexspi decoding

# LUTx.OPCODEy
_flexspi_opcode_enumset = (
  ('CMD_SDR', 0x01, None),
  ('CMD_DDR', 0x21, None),
  ('RADDR_SDR', 0x02, None),
  ('RADDR_DDR', 0x22, None),
  ('CADDR_SDR', 0x03, None),
  ('CADDR_DDR', 0x23, None),
  ('MODE1_SDR', 0x04, None),
  ('MODE1_DDR', 0x24, None),
  ('MODE2_SDR', 0x05, None),
  ('MODE2_DDR', 0x25, None),
  ('MODE4_SDR', 0x06, None),
  ('MODE4_DDR', 0x26, None),
  ('MODE8_SDR', 0x07, None),
  ('MODE8_DDR', 0x27, None),
  ('WRITE_SDR', 0x08, None),
  ('WRITE_DDR', 0x28, None),
  ('READ_SDR', 0x09, None),
  ('READ_DDR', 0x29, None),
  ('LEARN_SDR', 0x0a, None),
  ('LEARN_DDR', 0x2a, None),
  ('DATSZ_SDR', 0x0b, None),
  ('DATSZ_DDR', 0x2b, None),
  ('DUMMY_SDR', 0x0c, None),
  ('DUMMY_DDR', 0x2c, None),
  ('DUMMY_RWDS_SDR', 0x0d, None),
  ('DUMMY_RWDS_DDR', 0x2d, None),
  ('JMP_ON_CS', 0x1f, None),
  ('STOP', 0, None),
)

def flexspi_decodes(d):
  """setup additional flexspi field decodes not in the svd file"""
  p = d.FLEXSPI
  for i in range(64):
    r = p.registers['LUT%d' % i]
    f = r.OPCODE0
    f.enumvals = soc.make_enumvals(f, _flexspi_opcode_enumset)
    f = r.OPCODE1
    f.enumvals = soc.make_enumvals(f, _flexspi_opcode_enumset)

#-----------------------------------------------------------------------------

def rt1020_iomuxc_fixup(d):
  p = d.IOMUXC

  # remove some registers
  for i in range(16):
    p.remove('SW_MUX_CTL_PAD_GPIO_B0_%02d' % i)
    p.remove('SW_MUX_CTL_PAD_GPIO_B1_%02d' % i)
    p.remove('SW_PAD_CTL_PAD_GPIO_B0_%02d' % i)
    p.remove('SW_PAD_CTL_PAD_GPIO_B1_%02d' % i)

  for i in (2,3,4,5,6,7,8,9,20,21,22,23,24,25):
    p.remove('XBAR1_IN%02d_SELECT_INPUT' % i)

  for i in (2,3,4,5,6,7,8,9):
    p.remove('CSI_DATA%02d_SELECT_INPUT' % i)

#CSI_HSYNC_SELECT_INPUT          : 401f8420[31:0] = 0            CSI_HSYNC_SELECT_INPUT DAISY Register
#CSI_PIXCLK_SELECT_INPUT         : 401f8424[31:0] = 0            CSI_PIXCLK_SELECT_INPUT DAISY Register
#CSI_VSYNC_SELECT_INPUT          : 401f8428[31:0] = 0            CSI_VSYNC_SELECT_INPUT DAISY Register


  # add some registers
  add_regs = (
    'SW_MUX_CTL_PAD_GPIO_SD_B0_06',
    'SW_PAD_CTL_PAD_GPIO_SD_B0_06',
    'XBAR1_IN10_SELECT_INPUT',
    'XBAR1_IN12_SELECT_INPUT',
    'XBAR1_IN13_SELECT_INPUT',
  )
  for name in add_regs:
    r = soc.register()
    r.name = name
    r.size = 32
    p.insert(r)

  # change some offsets
  for i in range(7):
    r = p.registers['SW_MUX_CTL_PAD_GPIO_SD_B0_%02d' % i]
    r.offset = 0x13c + (i * 4)
    r = p.registers['SW_PAD_CTL_PAD_GPIO_SD_B0_%02d' % i]
    r.offset = 0x2b0 + (i * 4)

  for i in range(12):
    r = p.registers['SW_MUX_CTL_PAD_GPIO_SD_B1_%02d' % i]
    r.offset = 0x158 + (i * 4)
    r = p.registers['SW_PAD_CTL_PAD_GPIO_SD_B1_%02d' % i]
    r.offset = 0x2cc + (i * 4)

  for i in range(42):
    r = p.registers['SW_PAD_CTL_PAD_GPIO_EMC_%02d' % i]
    r.offset = 0x188 + (i * 4)

  for i in range(16):
    r = p.registers['SW_PAD_CTL_PAD_GPIO_AD_B0_%02d' % i]
    r.offset = 0x230 + (i * 4)
    r = p.registers['SW_PAD_CTL_PAD_GPIO_AD_B1_%02d' % i]
    r.offset = 0x270 + (i * 4)

  for i,v in enumerate((14,15,16,17,10,12,13,18,19)):
    r = p.registers['XBAR1_IN%02d_SELECT_INPUT' % v]
    r.offset = 0x4a0 + (i * 4)



def MIMXRT1021_fixup(d):
  d.soc_name = 'MIMXRT1021'
  d.cpu_info.nvicPrioBits = 4
  d.cpu_info.deviceNumInterrupts = 176
  # fix up some peripherals
  rt1020_iomuxc_fixup(d)
  # more decodes for peripheral registers
  flexspi_decodes(d)
  # memory
  d.insert(soc.make_peripheral('itcm', 0x00000000, 256 << 10, None, 'Instruction Tightly Coupled Memory'))
  d.insert(soc.make_peripheral('romcp', 0x00200000, 96 << 10, None, 'Boot ROM'))
  d.insert(soc.make_peripheral('dtcm', 0x20000000, 256 << 10, None, 'Data Tightly Coupled Memory'))
  d.insert(soc.make_peripheral('ocram', 0x20200000, 256 << 10, None, 'On Chip RAM'))
  d.insert(soc.make_peripheral('flexspi_memory', 0x60000000, 504 << 20, None, 'FlexSPI Memory'))
  d.insert(soc.make_peripheral('flexspi_rxfifo', 0x7fc00000, 4 << 20, None, 'FlexSPI Rx FIFO'))
  d.insert(soc.make_peripheral('flexspi_txfifo', 0x7f800000, 4 << 20, None, 'FlexSPI Tx FIFO'))
  d.insert(soc.make_peripheral('semc_memory', 0x80000000, 1536 << 20, None, 'SEMC Memory'))

s = soc_info()
s.name = 'MIMXRT1021DAG5A'
s.svd = 'MIMXRT1021'
s.fixups = (MIMXRT1021_fixup, cmregs.cm7_fixup,)
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not name in soc_db:
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/nxp/svd/%s.svd.gz' % info.svd
  #svd_file = './vendor/nxp/svd/%s.svd' % info.svd
  ui.put('%s: building %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  for f in info.fixups:
    f(device)
  return device


#-----------------------------------------------------------------------------
