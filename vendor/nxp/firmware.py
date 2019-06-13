#-----------------------------------------------------------------------------
"""

NXP Firmware Images

"""
#-----------------------------------------------------------------------------

import soc
import util

#-----------------------------------------------------------------------------
# IVT: The image vector table is a data structure in memory that tells the
# boot loader about the firmware.

def _format_IVT_tag(x):
  return ('(bad)', '(good)')[x == 0xd1]

def _format_IVT_length(x):
  return '(%d bytes)' % util.swap16(x)

def _format_IVT_version(x):
  return ('(bad)', '(good)')[x in (0x40, 0x41, 0x42, 0x43)]

_IVT_header_fieldset = (
  ('version', 31, 24, _format_IVT_version, 'version'),
  ('length', 23, 8, _format_IVT_length, 'length'),
  ('tag', 7, 0, _format_IVT_tag, 'tag'),
)

_IVT_regset = (
  ('header', 32, 0x00, _IVT_header_fieldset, 'IVT header'),
  ('entry', 32, 0x04, None, 'address of entry point'),
  ('dcd', 32, 0x0c, None, 'address of device configuration data'),
  ('boot_data', 32, 0x10, None, 'address of boot data'),
  ('this', 32, 0x14, None, 'address of IVT'),
  ('csf', 32, 0x18, None, 'address of command sequence file'),
)

#-----------------------------------------------------------------------------

def _boot_data_length_format(x):
  return '(%s)' % util.memsize(x)

_boot_data_length_fieldset = (
  ('length', 31, 0, _boot_data_length_format, 'length'),
)

_boot_data_regset = (
  ('start', 32, 0x0, None, 'address of bootable image'),
  ('length', 32, 0x4, _boot_data_length_fieldset, 'length of bootable image'),
  ('plugin', 32, 0x8, None, 'plugin flag'),
)

#-----------------------------------------------------------------------------

def _ncb_size_format(x):
  return '(%s)' % util.memsize(x)

_ncb_Size_fieldset = (
  ('size', 31, 0, _ncb_size_format, None),
)

_FlexSPI_NOR_Configuration_Block = (
 ('Tag', 32, 0x000, None, ''),
 ('Version', 32, 0x004, None, ''),
 ('readSampleClkSrc', 8, 0x00c, None, ''),
 ('csHoldTime', 8, 0x00d, None, ''),
 ('csSetupTime', 8, 0x00e, None, ''),
 ('columnAdressWidth', 8, 0x00f, None, ''),
 ('deviceModeCfgEnable', 8, 0x010, None, ''),
 ('deviceModeType', 8, 0x011, None, ''),
 ('waitTimeCfgCommands', 16, 0x012, None, ''),
 ('deviceModeSeq', 32, 0x014, None, ''),
 ('deviceModeArg', 32, 0x018, None, ''),
 ('configCmdEnable', 8, 0x01c, None, ''),
 ('configModeType', 8, 0x01d, None, ''),
 ('configCmdSeqs0', 32, 0x020, None, ''),
 ('configCmdSeqs1', 32, 0x024, None, ''),
 ('configCmdSeqs2', 32, 0x028, None, ''),
 ('cfgCmdArgs0', 32, 0x030, None, ''),
 ('cfgCmdArgs1', 32, 0x034, None, ''),
 ('cfgCmdArgs2', 32, 0x038, None, ''),
 ('controllerMiscOption', 32, 0x040, None, ''),
 ('deviceType', 8, 0x044, None, ''),
 ('sflashPadType', 8, 0x045, None, ''),
 ('serialClkFreq', 8, 0x046, None, ''),
 ('lutCustomSeqEnable', 8, 0x047, None, ''),
 ('sflashA1Size', 32, 0x050, _ncb_Size_fieldset, ''),
 ('sflashA2Size', 32, 0x054, _ncb_Size_fieldset, ''),
 ('sflashB1Size', 32, 0x058, _ncb_Size_fieldset, ''),
 ('sflashB2Size', 32, 0x05c, _ncb_Size_fieldset, ''),
 ('csPadSettingOverride', 32, 0x060, None, ''),
 ('sclkPadSettingOverride', 32, 0x064, None, ''),
 ('dataPadSettingOverride', 32, 0x068, None, ''),
 ('dqsPadSettingOverride', 32, 0x06c, None, ''),
 ('timeoutInMs', 32, 0x070, None, ''),
 ('commandInterval', 32, 0x074, None, ''),
 ('dataValidTime', 32, 0x078, None, ''),
 ('busyOffset', 16, 0x07c, None, ''),
 ('busyBitPolarity', 16, 0x07e, None, ''),
 ('lookupTable_00', 32, 0x080, None, ''),
 ('lookupTable_01', 32, 0x084, None, ''),
 ('lookupTable_02', 32, 0x088, None, ''),
 ('lookupTable_03', 32, 0x08c, None, ''),
 ('lookupTable_04', 32, 0x090, None, ''),
 ('lookupTable_05', 32, 0x094, None, ''),
 ('lookupTable_06', 32, 0x098, None, ''),
 ('lookupTable_07', 32, 0x09c, None, ''),
 ('lookupTable_08', 32, 0x0a0, None, ''),
 ('lookupTable_09', 32, 0x0a4, None, ''),
 ('lookupTable_0a', 32, 0x0a8, None, ''),
 ('lookupTable_0b', 32, 0x0ac, None, ''),
 ('lookupTable_0c', 32, 0x0b0, None, ''),
 ('lookupTable_0d', 32, 0x0b4, None, ''),
 ('lookupTable_0e', 32, 0x0b8, None, ''),
 ('lookupTable_0f', 32, 0x0bc, None, ''),
 ('lookupTable_10', 32, 0x0c0, None, ''),
 ('lookupTable_11', 32, 0x0c4, None, ''),
 ('lookupTable_12', 32, 0x0c8, None, ''),
 ('lookupTable_13', 32, 0x0cc, None, ''),
 ('lookupTable_14', 32, 0x0d0, None, ''),
 ('lookupTable_15', 32, 0x0d4, None, ''),
 ('lookupTable_16', 32, 0x0d8, None, ''),
 ('lookupTable_17', 32, 0x0dc, None, ''),
 ('lookupTable_18', 32, 0x0e0, None, ''),
 ('lookupTable_19', 32, 0x0e4, None, ''),
 ('lookupTable_1a', 32, 0x0e8, None, ''),
 ('lookupTable_1b', 32, 0x0ec, None, ''),
 ('lookupTable_1c', 32, 0x0f0, None, ''),
 ('lookupTable_1d', 32, 0x0f4, None, ''),
 ('lookupTable_1e', 32, 0x0f8, None, ''),
 ('lookupTable_1f', 32, 0x0fc, None, ''),
 ('lookupTable_20', 32, 0x100, None, ''),
 ('lookupTable_21', 32, 0x104, None, ''),
 ('lookupTable_22', 32, 0x108, None, ''),
 ('lookupTable_23', 32, 0x10c, None, ''),
 ('lookupTable_24', 32, 0x110, None, ''),
 ('lookupTable_25', 32, 0x114, None, ''),
 ('lookupTable_26', 32, 0x118, None, ''),
 ('lookupTable_27', 32, 0x11c, None, ''),
 ('lookupTable_28', 32, 0x120, None, ''),
 ('lookupTable_29', 32, 0x124, None, ''),
 ('lookupTable_2a', 32, 0x128, None, ''),
 ('lookupTable_2b', 32, 0x12c, None, ''),
 ('lookupTable_2c', 32, 0x130, None, ''),
 ('lookupTable_2d', 32, 0x134, None, ''),
 ('lookupTable_2e', 32, 0x138, None, ''),
 ('lookupTable_2f', 32, 0x13c, None, ''),
 ('lookupTable_30', 32, 0x140, None, ''),
 ('lookupTable_31', 32, 0x144, None, ''),
 ('lookupTable_32', 32, 0x148, None, ''),
 ('lookupTable_33', 32, 0x14c, None, ''),
 ('lookupTable_34', 32, 0x150, None, ''),
 ('lookupTable_35', 32, 0x154, None, ''),
 ('lookupTable_36', 32, 0x158, None, ''),
 ('lookupTable_37', 32, 0x15c, None, ''),
 ('lookupTable_38', 32, 0x160, None, ''),
 ('lookupTable_39', 32, 0x164, None, ''),
 ('lookupTable_3a', 32, 0x168, None, ''),
 ('lookupTable_3b', 32, 0x16c, None, ''),
 ('lookupTable_3c', 32, 0x170, None, ''),
 ('lookupTable_3d', 32, 0x174, None, ''),
 ('lookupTable_3e', 32, 0x178, None, ''),
 ('lookupTable_3f', 32, 0x17c, None, ''),
 ('lutCustomSeq_00', 32, 0x180, None, ''),
 ('lutCustomSeq_01', 32, 0x184, None, ''),
 ('lutCustomSeq_02', 32, 0x188, None, ''),
 ('lutCustomSeq_03', 32, 0x18c, None, ''),
 ('lutCustomSeq_04', 32, 0x190, None, ''),
 ('lutCustomSeq_05', 32, 0x194, None, ''),
 ('lutCustomSeq_06', 32, 0x198, None, ''),
 ('lutCustomSeq_07', 32, 0x19c, None, ''),
 ('lutCustomSeq_08', 32, 0x1a0, None, ''),
 ('lutCustomSeq_09', 32, 0x1a4, None, ''),
 ('lutCustomSeq_0a', 32, 0x1a8, None, ''),
 ('lutCustomSeq_0b', 32, 0x1ac, None, ''),
 ('pageSize', 32, 0x1c0, _ncb_Size_fieldset, ''),
 ('sectorSize', 32, 0x1c4, _ncb_Size_fieldset, ''),
 ('ipCmdSerialClkFreq', 32, 0x1c8, None, ''),
 ('isUniformBlockSize', 32, 0x1c9, None, ''),
 ('serialNorType', 8, 0x1cc, None, ''),
 ('needExitNoCmdMode', 32, 0x1cd, None, ''),
 ('halfClkForNonReadCmd', 8, 0x1ce, None, ''),
 ('needrestorNoCmdMode', 8, 0x1cf, None, ''),
 ('blockSize', 32, 0x1d0, _ncb_Size_fieldset, ''),
)

#-----------------------------------------------------------------------------

class firmware:

  def __init__(self, cpu):
    self.cpu = cpu
    self.menu = (
      ('info', self.cmd_info),
    )

  def cmd_info(self, ui,args):
    """display firmware information"""
    # nor
    ui.put('NOR Configuration Block\n')
    nor = soc.make_peripheral('ncb', 0x60000000, 0x200, _FlexSPI_NOR_Configuration_Block, 'NOR Configuration Block')
    nor.bind_cpu(self.cpu)
    ui.put('%s\n\n' % nor.display(fields=True))
    # ivt
    ui.put('Image Vector Table\n')
    ivt = soc.make_peripheral('ivt', 0x60001000, 32 << 2, _IVT_regset, 'Image Vector Table')
    ivt.bind_cpu(self.cpu)
    ui.put('%s\n\n' % ivt.display(fields=True))
    # boot_data
    boot_data = ivt.boot_data.rd()
    if boot_data != 0:
      ui.put('Boot Data\n')
      bd =  soc.make_peripheral('boot_data', boot_data, 3 << 2, _boot_data_regset, 'Boot Data')
      bd.bind_cpu(self.cpu)
      ui.put('%s\n\n' % bd.display(fields=True))

#-----------------------------------------------------------------------------
