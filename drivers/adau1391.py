# -----------------------------------------------------------------------------
"""

Analog Devices ADAU1391 Stereo CODEC

"""
# -----------------------------------------------------------------------------

import util

# -----------------------------------------------------------------------------

adau1391_regset = (
  (0x4000, 'Clock_Ctl'),
  (0x4002, 'PLL_Ctl'),
  (0x4008, 'Mic_Jack_Detect'),
  (0x4009, 'Rec_Power_Mgmt'),
  (0x400A, 'Rec_Mixer_Left0'),
  (0x400B, 'Rec_Mixer_Left1'),
  (0x400C, 'Rec_Mixer_Right0'),
  (0x400D, 'Rec_Mixer_Right1'),
  (0x400E, 'Left_Diff_Input_Vol'),
  (0x400F, 'Right_Diff_Input_Vol'),
  (0x4010, 'Record_Mic_Bias'),
  (0x4011, 'ALC0'),
  (0x4012, 'ALC1'),
  (0x4013, 'ALC2'),
  (0x4014, 'ALC3'),
  (0x4015, 'Serial_Port0'),
  (0x4016, 'Serial_Port1'),
  (0x4017, 'Converter0'),
  (0x4018, 'Converter1'),
  (0x4019, 'ADC_Ctl'),
  (0x401A, 'Left_Digital_Vol'),
  (0x401B, 'Right_Digital_Vol'),
  (0x401C, 'Play_Mixer_Left0'),
  (0x401D, 'Play_Mixer_Left1'),
  (0x401E, 'Play_Mixer_Right0'),
  (0x401F, 'Play_Mixer_Right1'),
  (0x4020, 'Play_LR_Mixer_Left'),
  (0x4021, 'Play_LR_Mixer_Right'),
  (0x4022, 'Play_LR_Mixer_Mono'),
  (0x4023, 'Play_HP_Left_Vol'),
  (0x4024, 'Play_HP_Right_Vol'),
  (0x4025, 'Line_Output_Left_Vol'),
  (0x4026, 'Line_Output_Right_Vol'),
  (0x4027, 'Play_Mono_Output'),
  (0x4028, 'Pop_Click_Suppress'),
  (0x4029, 'Play_Power_Mgmt'),
  (0x402A, 'DAC_Ctl0'),
  (0x402B, 'DAC_Ctl1'),
  (0x402C, 'DAC_Ctl2'),
  (0x402D, 'Serial_Port_Pad'),
  (0x402F, 'Ctl_Port_Pad0'),
  (0x4030, 'Ctl_Port_Pad1'),
  (0x4031, 'Jack_Detect_Pin'),
  (0x4036, 'Dejitter_Ctl'),
)

class adau1391:
  """Analog Devices ADAU1391 Stereo CODEC"""

  def __init__(self, bus, adr):
    self.bus = bus
    self.adr = adr
    self.hw_init = False
    self.menu = (
      ('init', self.cmd_init),
      ('status', self.cmd_status),
    )

  def rdbuf(self, ofs, n):
    """read a buffer of n bytes from the codec"""
    self.bus.wr(self.adr, [(ofs >> 8) & 0xff, ofs & 0xff])
    return self.bus.rd(self.adr, n)

  def wrbuf(self, ofs, buf):
    """write a buffer of bytes to the codec"""
    x = [(ofs >> 8) & 0xff, ofs & 0xff].extend(buf)
    self.bus.wr(self.adr, x)

  def rd(self, ofs):
    """read a codec register"""
    return self.rdbuf(ofs, 1)[0]

  def pwrup(self):
    """power up sequence"""
    # TODO

  def cmd_init(self, ui, args):
    """initialise dac hardware"""
    if self.hw_init:
      return
    self.bus.io.cmd_init(ui, args)
    # codec power up
    self.pwrup()
    self.hw_init = True
    ui.put('adau1391 init: ok\n')

  def cmd_status(self, ui, args):
    """display dac status"""
    s = []
    for (ofs, name) in adau1391_regset:
      val = self.rd(ofs)
      s.append(['0x%04x' % ofs, ': 0x%02x' % val, name])
    ui.put('%s\n' % util.display_cols(s))

# -----------------------------------------------------------------------------
