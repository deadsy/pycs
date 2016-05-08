# pycs
Python Based ARM CoreSight Debug and Trace Tools

 * PyCS is a python based JTAG/SWD debugger for ARM chips.
 * Its current focus is systems using Cortex-M ARM CPUs.
 * It uses a Segger JLINK Debug Probe to communicate with the ARM CPU. 

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
 * mb1035b (STM32F3 Discovery Board)
 * saml21 (Atmel SAM L21 Xplained Pro Board)

## Hooking up ST Development Boards

The ST boards have a 6 pin SWD debug connector.
The JLINK has a 20 pin connector.

 * Pin 1 (VDD_TARGET) - No Connect (this is NOT a target reference voltage!)
 * Pin 2 (SWCLK) - Pin 9 (SWCLK) on JLINK
 * Pin 3 (GND) - Pin 4 (GND) on JLINK
 * Pin 4 (SWDIO) - Pin 7 (SWDIO) on JLINK
 * Pin 5 (NRST) - Pin 15 (RESET) on JLINK
 * Pin 6 (SWO) - Pin 13 (SWO) on JLINK (optional)
 * 3V Vdd - Pin 1 (VTref) on JLINK 

Leave the ST-Link/Discovery jumpers installed so the debug signals are passed to the Discovery CPU.








