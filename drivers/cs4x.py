# -----------------------------------------------------------------------------
"""

Cirrus Logic CS4x Codecs/DACs

"""
# -----------------------------------------------------------------------------

import util

# -----------------------------------------------------------------------------

cs43l22_regset = (
  (0x01, 'ID'),
  (0x02, 'Power Ctl 1'),
  (0x04, 'Power Ctl 2'),
  (0x05, 'Clocking Ctl'),
  (0x06, 'Interface Ctl 1'),
  (0x07, 'Interface Ctl 2'),
  (0x08, 'Passthrough A Select'),
  (0x09, 'Passthrough B Select'),
  (0x0A, 'Analog ZC and SR Settings'),
  (0x0C, 'Passthrough Gang Control'),
  (0x0D, 'Playback Ctl 1'),
  (0x0E, 'Misc. Ctl'),
  (0x0F, 'Playback Ctl 2'),
  (0x14, 'Passthrough A Vol'),
  (0x15, 'Passthrough B Vol'),
  (0x1A, 'PCMA Vol'),
  (0x1B, 'PCMB Vol'),
  (0x1C, 'BEEP Freq On Time'),
  (0x1D, 'BEEP Vol Off Time'),
  (0x1E, 'BEEP Tone Cfg'),
  (0x1F, 'Tone Ctl'),
  (0x20, 'Master A Vol'),
  (0x21, 'Master B Vol'),
  (0x22, 'Headphone A Volume'),
  (0x23, 'Headphone B Volume'),
  (0x24, 'Speaker A Volume'),
  (0x25, 'Speaker B Volume'),
  (0x26, 'Channel Mixer & Swap'),
  (0x27, 'Limit Ctl 1 Thresholds'),
  (0x28, 'Limit Ctl 2 Release Rate'),
  (0x29, 'Limiter Attack Rate'),
  (0x2E, 'Overflow & Clock Status'),
  (0x2F, 'Battery Compensation'),
  (0x30, 'VP Battery Level'),
  (0x31, 'Speaker Status'),
  (0x34, 'Charge Pump Frequency'),
)

class cs43l22(object):
  """Cirrus Logic CS43L22 Stereo DAC"""

  def __init__(self, bus, adr, reset):
    self.bus = bus
    self.adr = adr
    self.reset = reset
    self.hw_init = False
    self.menu = (
      ('init', self.cmd_init),
      ('status', self.cmd_status),
    )

  def rd(self, ofs):
    """read a dac register"""
    self.bus.wr(self.adr, [ofs,])
    return self.bus.rd(self.adr, 1)[0]

  def wr(self, ofs, val):
    """write a dac register"""
    self.bus.wr(self.adr, [ofs, val])

  def pwrup(self):
    """power up sequence"""
    # reset the dac
    self.reset(0)
    self.reset(1)
    # see sect 4.11 of manual
    self.wr(0x00,0x99)
    self.wr(0x47,0x80)
    self.wr(0x32, self.rd(0x32) | (1 << 7))
    self.wr(0x32, self.rd(0x32) & ~(1 << 7))
    self.wr(0x00,0x00)

  def cmd_init(self, ui, args):
    """initialise dac hardware"""
    if self.hw_init:
      return
    self.bus.io.cmd_init(ui, args)
    # dac power up
    self.pwrup()
    self.hw_init = True
    ui.put('cs43l22 init: ok\n')

  def cmd_status(self, ui, args):
    """display dac status"""
    s = []
    for (ofs, name) in cs43l22_regset:
      val = self.rd(ofs)
      s.append(['0x%02x' % ofs, ': 0x%02x' % val, name])
    ui.put('%s\n' % util.display_cols(s))

# -----------------------------------------------------------------------------
