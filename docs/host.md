# Host System

PyCS is developed on a Linux box with Python 2.7.11.
PyCS is written in Python and is not very host specific.
I've never run it on Mac or Windows, but it will probably work with a bit of modification.
Mac being more Unix-y probably has less issues than Windows.

Likely problem areas:

 * CLI weirdness
 * Need platform specific libraries JLINK operation.
 * Trouble compiling the C code. (needs gcc)
 * Trouble compiling the ASM code. (needs an ARM gcc tool)

Mac/Windows users- I'm not going to work on it, so you are on your own. Let me know if you have any patches.




