#------------------------------------------------------------------------------
"""
FT2232 Based JTAG Drivers

Note:
This code uses ftdi.py and usbtools.py both taken from the pyftdi project.
The pyftdi project has some JTAG functions but the JTAG api and their
method for storing bit streams is different from the rest of this code,
so I've only borrowed the ftdi specific portions.
"""
#-----------------------------------------------------------------------------

import time
import array
import sys
import tap
from ftdi import Ftdi
import usbtools

#------------------------------------------------------------------------------

_TRST_TIME = 0.01
_SRST_TIME = 0.01
_READ_RETRIES = 4

_MHz = 1000000.0
_KHz = 1000.0
_FREQ = 6.0 * _MHz

#------------------------------------------------------------------------------
# JTAG/GPIO Lines in MPSSE Mode

_TCK    = (1 << 0) # output, normally low
_TDI    = (1 << 1) # output, sampled on rising edge of tck
_TDO    = (1 << 2) # input
_TMS    = (1 << 3) # output, sampled on rising edge of tck
_GPIOL0 = (1 << 4)
_GPIOL1 = (1 << 5)
_GPIOL2 = (1 << 6)
_GPIOL3 = (1 << 7)
_GPIOH0 = (1 << 8)
_GPIOH1 = (1 << 9)
_GPIOH2 = (1 << 10)
_GPIOH3 = (1 << 11)
_GPIOH4 = (1 << 12)
_GPIOH5 = (1 << 13)
_GPIOH6 = (1 << 14)
_GPIOH7 = (1 << 15)

# Commands in MPSSE Mode
_MPSSE_WRITE_NEG = 0x01   # Write TDI/DO on negative TCK/SK edge
_MPSSE_BITMODE   = 0x02   # Write bits, not bytes
_MPSSE_READ_NEG  = 0x04   # Sample TDO/DI on negative TCK/SK edge
_MPSSE_LSB       = 0x08   # LSB first
_MPSSE_DO_WRITE  = 0x10   # Write TDI/DO
_MPSSE_DO_READ   = 0x20   # Read TDO/DI
_MPSSE_WRITE_TMS = 0x40   # Write TMS/CS

#-----------------------------------------------------------------------------
# MSB/LSB for 16 bit values

def _msb(val): return (val >> 8) & 255
def _lsb(val): return val & 255

#-----------------------------------------------------------------------------
# tms bit sequences

def tms_mpsse(bits):
    """convert a tms bit sequence to an mpsee (len, bits) tuple"""
    n = len(bits)
    assert (n > 0) and (n <= 7)
    x = 0
    # tms is shifted lsb first
    for i in range(n - 1, -1, -1):
        x = (x << 1) + bits[i]
    # only bits 0 thru 6 are shifted on tms - tdi is set to bit 7 (and is left there)
    # len = n means clock out n + 1 bits
    return (n - 1, x & 127)

#------------------------------------------------------------------------------

class ft2232:

    def open_ft2232(self, vps, itf, sn):
        # find the device on USB
        devices = usbtools.UsbTools.find_all(vps)
        if sn is not None:
            # filter based on device serial number
            devices = [dev for dev in devices if dev[2] == sn]
        if len(devices) == 0:
            raise IOError("No such device")
        self.vid = devices[0][0]
        self.pid = devices[0][1]
        self.sn = devices[0][2]
        self.ftdi = Ftdi()
        self.freq = self.ftdi.open_mpsse(self.vid, self.pid, itf, serial = self.sn, frequency = _FREQ)
        self.wrbuf = array.array('B')
        self.gpio_init()
        self.state_reset()
        self.sir_end_state = 'IDLE'
        self.sdr_end_state = 'IDLE'

    def __del__(self):
        if self.ftdi:
            self.ftdi.close()

    def flush(self):
        """flush the write buffer to the ft2232"""
        if len(self.wrbuf) > 0:
            self.ftdi.write_data(self.wrbuf)
            del self.wrbuf[0:]

    def write(self, buf, flush = False):
        """queue write data to send to ft2232"""
        self.wrbuf.extend(buf)
        if flush:
            self.flush()

    def state_x(self, dst):
        """change the TAP state from self.state to dst"""
        if self.state == dst:
          return
        tms = tms_mpsse(tap.lookup(self.state, dst))
        cmd = _MPSSE_WRITE_TMS | _MPSSE_BITMODE | _MPSSE_LSB | _MPSSE_WRITE_NEG
        self.write((cmd, tms[0], tms[1]), True)
        self.state = dst

    def state_reset(self):
        """from *any* state go to the reset state"""
        self.state = '*'
        self.state_x('RESET')

    def shift_data(self, tdi, tdo, end_state):
        """
        write (and possibly read) a bit stream from the JTAGkey
        tdi - bit buffer of data to be written to the JTAG TDI pin
        tdo - bit buffer for the data read from the JTAG TDO pin (optional)
        end_state - leave the TAP state machine in this state
        """
        wr = tdi.get()
        io_bits = tdi.n - 1
        io_bytes = io_bits >> 3
        io_bits &= 0x07
        last_bit = (wr[io_bytes] << (7 - io_bits)) & 128

        if tdo is not None:
            read_cmd = _MPSSE_DO_READ
            read_len = io_bytes + 1
            if io_bits:
                read_len += 1
        else:
            read_cmd = 0
            read_len = 0

        # write out the full bytes
        if io_bytes:
            cmd = read_cmd | _MPSSE_DO_WRITE | _MPSSE_LSB | _MPSSE_WRITE_NEG
            num = io_bytes - 1
            self.write((cmd, _lsb(num), _msb(num)))
            self.write(wr[0:io_bytes])

        # write out the remaining bits
        if io_bits:
            cmd = read_cmd | _MPSSE_DO_WRITE | _MPSSE_LSB | _MPSSE_BITMODE | _MPSSE_WRITE_NEG
            self.write((cmd, io_bits - 1, wr[io_bytes]))

        # the last bit of output data is bit 7 of the tms value (goes onto tdi)
        # continue to read to get the last bit of tdo data
        cmd = read_cmd | _MPSSE_WRITE_TMS | _MPSSE_BITMODE | _MPSSE_LSB | _MPSSE_WRITE_NEG
        tms = tms_mpsse(tap.lookup(self.state, end_state))
        self.write((cmd, tms[0], tms[1] | last_bit))
        self.state = end_state

        # if we are only writing, return
        if tdo is None:
            self.flush()
            return

        # make the ft2232 flush its data back to the PC
        self.write((Ftdi.SEND_IMMEDIATE,), True)
        rd = self.ftdi.read_data_bytes(read_len, _READ_RETRIES)

        if io_bits:
            # the n partial bits are in the top n bits of the byte
            # move them down to the bottom
            rd[-2] >>= (8 - io_bits)

        # get the last bit from the tms response byte (last byte)
        last_bit = (rd[-1] >> (7 - tms[0])) & 1
        last_bit <<= io_bits

        # add the last bit
        if io_bits:
            # drop the tms response byte
            del rd[-1]
            # or it onto the io_bits byte
            rd[-1] |= last_bit
        else:
            # replace the tms response byte
            rd[-1] = last_bit

        # copy to the bit buffer
        tdo.set(tdi.n, rd)

    def scan_ir(self, tdi, tdo = None):
        """write (and possibly read) a bit stream through the IR in the JTAG chain"""
        self.state_x('IRSHIFT')
        self.shift_data(tdi, tdo, self.sir_end_state)

    def scan_dr(self, tdi, tdo = None):
        """write (and possibly read) a bit stream through the DR in the JTAG chain"""
        self.state_x('DRSHIFT')
        self.shift_data(tdi, tdo, self.sdr_end_state)

    def gpio_init(self):
        """setup the gpio lines"""
        self.gpio_dir = _TCK | _TDI | _TMS
        self.gpio_val = 0
        self.ftdi.write_data((Ftdi.SET_BITS_LOW, _lsb(self.gpio_val), _lsb(self.gpio_dir)))
        self.ftdi.write_data((Ftdi.SET_BITS_HIGH, _msb(self.gpio_val), _msb(self.gpio_dir)))

    def gpio_wr(self, gpio, val):
        """write a gpio pin"""
        self.gpio_dir |= gpio
        if val:
            self.gpio_val |= gpio
        else:
            self.gpio_val &= ~gpio
        if gpio <= _GPIOL3:
            self.ftdi.write_data((Ftdi.SET_BITS_LOW, _lsb(self.gpio_val), _lsb(self.gpio_dir)))
        else:
            self.ftdi.write_data((Ftdi.SET_BITS_HIGH, _msb(self.gpio_val), _msb(self.gpio_dir)))

    def gpio_rd(self, gpio):
        """read a gpio pin"""
        if gpio <= _GPIOL3:
            self.ftdi.write_data((Ftdi.GET_BITS_LOW,))
            val = self.ftdi.read_data_bytes(1, _READ_RETRIES)[0]
        else:
            self.ftdi.write_data((Ftdi.GET_BITS_HIGH,))
            val = self.ftdi.read_data_bytes(1, _READ_RETRIES)[0]
            val <<= 8
        return (val & gpio) != 0

#------------------------------------------------------------------------------
"""
Definitions and functions specific to the JTAGkey dongle
Amontec JTAGkey: http://www.amontec.com/
The JTAGkey devices have a FT2232D or FT2232H device (JTAGKey2)

FT2232 Connectivity

TCK    > TCK_OUT (gated by JTAG_OE_N)
TDI    > TDI_OUT (gated by JTAG_OE_N)
TDO    > TDO_IN
TMS    > TMS_OUT (gated by JTAG_OE_N)
GPIOL0 > JTAG_OE_N (active low)
GPIOL1 > VREF_N_IN
GPIOL2 > SRST_N_IN
GPIOL3 > not connected
GPIOH0 > TRST_N_OUT (gated by TRST_N_OE_N)
GPIOH1 > SRST_N_OUT (gated by SRST_N_OE_N)
GPIOH2 > TRST_N_OE_N
GPIOH3 > SRST_N_OE_N
GPIOH4 > not connected
GPIOH5 > not connected
GPIOH6 > not connected
GPIOH7 > not connected
"""

# gpio pins
_JTAG_OE_N = _GPIOL0
_VREF_N_IN = _GPIOL1
_SRST_N_IN = _GPIOL2
_TRST_N_OUT = _GPIOH0
_SRST_N_OUT = _GPIOH1
_TRST_N_OE_N = _GPIOH2
_SRST_N_OE_N = _GPIOH3

# usb vendor:product IDs
_jtagkey_vps = (
    (0x0403, 0x6010), # bus blaster jtagkey emulation
    (0x0403, 0xcff8), # amontec jtagkey
)

_jtagkey_itf = 1 # external jtag is on the first interface

class jtagkey(ft2232):

    def __init__(self, sn = None):
        """initialise the JTAGkey device"""
        self.open_ft2232(_jtagkey_vps, _jtagkey_itf, sn)
        # deassert resets
        self.gpio_wr(_TRST_N_OUT, 1)
        self.gpio_wr(_SRST_N_OUT, 1)
        # enable outputs
        self.gpio_wr(_TRST_N_OE_N, 0)
        self.gpio_wr(_SRST_N_OE_N, 0)
        self.gpio_wr(_JTAG_OE_N, 0)
        # check VREF and SRST
        assert self.gpio_rd(_VREF_N_IN) == False, '~VREF signal is not asserted. Target is disconnected or powered off.'
        assert self.gpio_rd(_SRST_N_IN) == True, '~SRST signal is asserted. Target is held in reset.'

    def trst(self):
        """pulse the test reset line"""
        self.gpio_wr(_TRST_N_OUT, 0)
        time.sleep(_TRST_TIME)
        self.gpio_wr(_TRST_N_OUT, 1)
        self.state_reset()

    def srst(self):
        """pulse the system reset line"""
        self.gpio_wr(_SRST_N_OUT, 0)
        time.sleep(_SRST_TIME)
        self.gpio_wr(_SRST_N_OUT, 1)

    def __str__(self):
        s = []
        s.append('JTAGKey usb %04x:%04x serial %r' % (self.vid, self.pid, self.sn))
        s.append('%s @ %.1f MHz' % (self.ftdi.ic_name, (self.freq / _MHz)))
        return ', '.join(s)

#------------------------------------------------------------------------------
