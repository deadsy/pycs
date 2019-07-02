# Host System

PyCS is developed on a Linux box with Python 3.

## Dependencies
  * sudo -H pip3 install hid
  * etc...

## Other Platforms

I've never run it on Mac or Windows, but it will probably work with a bit of modification.
Mac being more Unix-like probably has less issues than Windows.

Likely problem areas:

 * CLI weirdness
 * Need platform specific libraries for JLINK operation.
 * Trouble compiling the darm C code. (needs gcc)

Mac/Windows users- I'm not going to work on it, so you are on your own. Let me know if you have any patches.
