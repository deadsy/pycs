# SWD Debug Interfaces

PyCS currently support two debug interfaces.

## Segger JLINK

 * https://www.segger.com/jlink-debug-probes.html
 * The Base and EDU devices have been tested, but anything with SWD capability should work.

Low level access to the CPU is done via the JLINK device library.
This is a shared object file that must be downloaded from Segger separately.

See- https://www.segger.com/jlink-software.html

The library from this download is copied to the ./lib32 or ./lib64 directory.

    tar zxvf JLink_Linux_V512e_x86_64.tgz
    cp ./JLink_Linux_V512e_x86_64/libjlinkarm.so.5.12.5 ./lib64
    cd ./lib64
    ln -sf  ./libjlinkarm.so.5.12.5 ./libjlinkarm.so.5
    ln -sf  ./libjlinkarm.so.5.12.5 ./libjlinkarm.so

Note: The libraries for MacOS and Windows systems probably work, but I haven't tested them.

## STLinkV2

 * The STLinkV2 interface is supported directly by PyCS.
 * STLinkV2 is commonly built-in to ST development boards.
 * It is also available as a stand-alone USB dongle E.g. https://www.adafruit.com/products/2548
 * STLinkV2 can be used with any Cortex-M chip - not just ST chips.

Note: STLinkV2 provides no direct support for 16-bit read and writes. This is occasionally an issue.
E.g.- writing to flash on certain ST parts. In these cases the read/write must be done using assembly language
routines that are downloaded to device RAM and run from there.

## CMSIS-DAP

Not currently supported.


