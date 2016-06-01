#-----------------------------------------------------------------------------
"""

SoC file for stm32 devices

Read in the SVD file for a named SoC.
Run fixup functions to correct any SVD inadequecies.

"""
#-----------------------------------------------------------------------------

import soc

#-----------------------------------------------------------------------------
# ST typically doesn't provide cpu information in the SVD files
# These functions are used to provide the required data.

def cm4_fixup(d):
  d.cpu.name = 'CM4'
  d.cpu.nvicPrioBits = 4

#-----------------------------------------------------------------------------
# build a database of SoC devices

class soc_info(object):
  def __init__(self):
    pass

soc_db = {}

s = soc_info()
s.name = 'STM32F407xx'
s.svd = 'STM32F40x'
s.cpu_fixup = cm4_fixup
soc_db[s.name] = s

#-----------------------------------------------------------------------------

def get_device(ui, name):
  """return the device structure for the named SoC"""
  if not soc_db.has_key(name):
    assert False, 'unknown SoC name %s' % name
    return None
  info = soc_db[name]
  svd_file = './vendor/st/svd/%s.svd.gz' % info.svd
  ui.put('%s: building %s\n' % (name, svd_file))
  device = soc.build_device(svd_file)
  info.cpu_fixup(device)
  return device

#-----------------------------------------------------------------------------

#class soc(object):
  #"""stm32 SoC"""

  #def __init__(self, cpu, info):
    #self.cpu = cpu
    #self.info = info
    #self.exceptions = cortexm.build_exceptions(info['vtable'])
    #self.memmap = self.build_memmap()

    #self.menu = (
      #('exceptions', self.cmd_exceptions),
    #)

  #def build_memmap(self):
    #"""build the soc memory map"""
    ## TODO - build the tweaked map
    #return self.info['memmap']

  #def cmd_exceptions(self, ui, args):
    #"""display exceptions table"""
    #ui.put('%s\n' % cortexm.exceptions_str(self.cpu, self))

#-----------------------------------------------------------------------------
