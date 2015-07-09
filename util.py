# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
"""
General Utilities
"""
#------------------------------------------------------------------------------

bad_argc = 'bad number of arguments\n'
inv_arg = 'invalid argument\n'

limit_64 = (0, 0xffffffffffffffff)
limit_32 = (0, 0xffffffff)

#-----------------------------------------------------------------------------
# endian conversions

def identity(x):
    """identity - no changes"""
    return x

def ltob16(x):
    """little to big endian 16 bits"""
    return ((x & 0xff00) >> 8) | \
            ((x & 0x00ff) << 8)

def ltob32(x):
    """little to big endian 32 bits"""
    return ((x & 0xff000000) >> 24) | \
           ((x & 0x00ff0000) >> 8) | \
           ((x & 0x0000ff00) << 8) | \
           ((x & 0x000000ff) << 24)

def btol32(x):
    return ltob32(x)

#------------------------------------------------------------------------------

def wrong_argc(ui, args, valid):
    """return True if argc is not valid"""
    argc = len(args)
    if argc in valid:
        return False
    else:
        ui.put(bad_argc)
        return True

#------------------------------------------------------------------------------

def int_arg(ui, arg, limits, base):
    """convert a number string to an integer - or None"""
    try:
        val = int(arg, base)
    except ValueError:
        ui.put(inv_arg)
        return None
    if (val < limits[0]) or (val > limits[1]):
        ui.put(inv_arg)
        return None
    return val

#-----------------------------------------------------------------------------

def sex_arg(ui, arg, width):
    """sign extend a 32 bit argument to 64 bits"""
    limits = (limit_32, limit_64)[width == 64]
    val = int_arg(ui, arg, limits, 16)
    if val == None:
        return None
    if (len(arg) == 8) and (width == 64):
        if val & (1 << 31):
            val |= (0xffffffff << 32)
    return val

#-----------------------------------------------------------------------------

def align_adr(adr, width):
    """align address to a width bits boundary"""
    mask = (width >> 3) - 1
    return adr & ~mask

#-----------------------------------------------------------------------------

def nbytes_to_nwords(n, width):
    """how many width-bit words in n bytes?"""
    (mask, shift) = ((3, 2), (7, 3))[width == 64]
    return ((n + mask) & ~mask) >> shift

#------------------------------------------------------------------------------

def m2f_args(ui, width, args):
    """memory to file arguments: return (adr, n, name) or None"""
    if wrong_argc(ui, args, (2, 3)):
        return None
    adr = sex_arg(ui, args[0], width)
    if adr == None:
        return None
    n = int_arg(ui, args[1], (1, 0xffffffff), 16)
    if n == None:
        return None
    name = 'mem.bin'
    if len(args) == 3:
        name = args[2]
    return (adr, n, name)

#------------------------------------------------------------------------------

def m2d_args(ui, width, args):
    """memory to display arguments: return (adr, n) or None"""
    if wrong_argc(ui, args, (1, 2)):
        return
    adr = sex_arg(ui, args[0], 32)
    if adr == None:
        return
    if len(args) == 2:
        n = int_arg(ui, args[1], (1, 0xffffffff), 16)
        if n == None:
            return
    else:
        n = 0x40
    return (adr, n)

#-----------------------------------------------------------------------------
# bit field manipulation

def maskshift(field):
    """return a mask and shift defined by field"""
    if len(field) == 1:
        return (1 << field[0], field[0])
    else:
        return (((1 << (field[0] - field[1] + 1)) - 1) << field[1], field[1])

def bits(val, field):
    """return the bits (masked and shifted) from the value"""
    (mask, shift) = maskshift(field)
    return (val & mask) >> shift

def masked(val, field):
    """return the bits (masked only) from the value"""
    return val & maskshift(field)[0]

#-----------------------------------------------------------------------------

def format_dec(val):
    return '%d' % val

def format_hex32(val):
    return '%08x' % val

def bitfield_v(val, fields, col = 15):
    """
    return a string of bit field components formatted vertically
    val: the value to be split into bit fields
    fields: a tuple of (name, output_function, (bit_hi, bit_lo)) tuples
    """
    fmt = '%%-%ds: %%s' % col
    s = []
    for (name, func, field) in fields:
        s.append(fmt % (name, func(bits(val, field))))
    return '\n'.join(s)

def bitfield_h(val, fields):
    """
    return a string of bit field components formatted horizontally
    val: the value to be split into bit fields
    fields: a tuple of (name, output_function, (bit_hi, bit_lo)) tuples
    """
    l = []
    for (name, func, field) in fields:
        if func is None:
            if bits(val, field) != 0:
                l.append('%s' % name)
        elif name is None:
            s = func(bits(val, field))
            if s:
                l.append(s)
        else:
            l.append(('%s(%s)' % (name, func(bits(val, field)))))
    return ' '.join(l)

#------------------------------------------------------------------------------

class progress:
    """percent complete and activity indication"""

    def __init__(self, ui, div, nmax):
        """
        progress indicator
        div = slash speed, larger is slower
        nmax = maximum value, 100%
        """
        self.ui = ui
        self.nmax = nmax
        self.progress = ''
        self.div = div
        self.mask = (1 << div) - 1

    def erase(self):
        """erase the progress indication"""
        n = len(self.progress)
        self.ui.put(''.join(['\b' * n, ' ' * n, '\b' * n]))

    def update(self, n):
        """update the progress indication"""
        if n & self.mask == 0:
            self.erase()
            istr = '-\\|/'[(n >> self.div) & 3]
            pstr = '%d%% ' % ((100 * n) / self.nmax)
            self.progress = ''.join([pstr, istr])
            self.ui.put(self.progress)

#------------------------------------------------------------------------------
