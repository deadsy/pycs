# pycs
Python Based ARM CoreSight Debug and Trace Tools

 * PyCS is a python based JTAG/SWD debugger for ARM chips.
 * Its current focus is systems using Cortex-M ARM CPUs.
 * It uses a Segger JLINK Debug Probe to communicate with the ARM CPU. 
 * It reads the SoC SVD files to give full peripheral/register decode.

## What do I need?
 * A PC running Linux (with Python)
 * A Segger JLINK Device (https://www.segger.com/jlink-debug-probes.html) The Base and EDU devices have been tested, but anything with SWD capability should work.
 * A system with a Cortex-M ARM cpu.

Low level access to the CPU is done via the JLINK device library. This must be downloaded from Segger separately.

See- https://www.segger.com/jlink-software.html

The shared library from this download is copied to the ./lib32 or ./lib64 directory.

    tar zxvf JLink_Linux_V512e_x86_64.tgz
    cp ./JLink_Linux_V512e_x86_64/libjlinkarm.so.5.12.5 ./lib64
    cd ./lib64
    ln -sf  ./libjlinkarm.so.5.12.5 ./libjlinkarm.so.5
    ln -sf  ./libjlinkarm.so.5.12.5 ./libjlinkarm.so

Note: MacOS and Windows systems probably work, but I haven't tested them.

## Using the Tool

    $ ./pycs -t mb1035b
    
    pycs: ARM CoreSight Tool 1.0
    trying '/home/jasonh/work/pycs/lib64/libjlinkarm.so.5'...
    using '/home/jasonh/work/pycs/lib64/libjlinkarm.so.5'
    jlink library v51205 Apr 29 2016 15:06:27
    jlink device v93000 sn59305661 J-Link V9 compiled Mar 29 2016 18:46:37
    target voltage 2.955V
    
    mb1035b*> 


It has an interactive CLI.
 * '?' for menu help
 * '?' for command completion/argument help
 * TAB for command completion
 * 'help' for general help

## Features
 * display memory
 * disassemble memory
 * display system control registers
 * display peripheral registers
 * halt/go the cpu
 * measure counter frequencies
 * etc. etc.

## Current Targets
 * frdm_k64f (NXP Kinetis K64 Board)
 * mb1035b (STM32F3 Discovery Board)
 * mb997c (STM32F4 Discovery Board)
 * nRF51822 (Adafruit BLE USB Dongle) 
 * saml21 (Atmel SAM L21 Xplained Pro Board)


## Other Documents

 * [HOWTO hookup development boards](https://github.com/deadsy/pycs/blob/master/docs/hookup.md)
