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

_boot_data_regset = (
  ('start', 32, 0x0, None, 'address of bootable image'),
  ('length', 32, 0x4, None, 'length of bootable image'),
  ('plugin', 32, 0x8, None, 'plugin flag'),
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
 ('sflashA1Size', 32, 0x050, None, ''),
 ('sflashA2Size', 32, 0x054, None, ''),
 ('sflashB1Size', 32, 0x058, None, ''),
 ('sflashB2Size', 32, 0x05c, None, ''),
 ('csPadSettingOverride', 32, 0x060, None, ''),
 ('sclkPadSettingOverride', 32, 0x064, None, ''),
 ('dataPadSettingOverride', 32, 0x068, None, ''),
 ('dqsPadSettingOverride', 32, 0x06c, None, ''),
 ('timeoutInMs', 32, 0x070, None, ''),
 ('commandInterval', 32, 0x074, None, ''),
 ('dataValidTime', 32, 0x078, None, ''),
 ('busyOffset', 16, 0x07c, None, ''),
 ('busyBitPolarity', 16, 0x07e, None, ''),
 ('lookupTable', 32, 0x080, None, ''), # 0..63
 ('lutCustomSeq', 32, 0x180, None, ''), # 0..11
 ('pageSize', 32, 0x1c0, None, ''),
 ('sectorSize', 32, 0x1c4, None, ''),
 ('ipCmdSerialClkFreq', 32, 0x1c8, None, ''),
 ('isUniformBlockSize', 32, 0x1c9, None, ''),
 ('serialNorType', 8, 0x1cc, None, ''),
 ('needExitNoCmdMode', 32, 0x1cd, None, ''),
 ('halfClkForNonReadCmd', 8, 0x1ce, None, ''),
 ('needrestorNoCmdMode', 8, 0x1cf, None, ''),
 ('blockSize', 32, 0x1d0, None, ''),
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
    p = soc.make_peripheral('ivt', 0x60001000, 128, _IVT_regset, 'Image Vector Table')
    p.bind_cpu(self.cpu)
    ui.put('%s\n' % p.display(fields=True))

#-----------------------------------------------------------------------------
