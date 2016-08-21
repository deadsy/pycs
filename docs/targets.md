# Target Support

There are many Cortex-M based platforms in the world.
No single tool supports all of them.
Most debuggers are written in C and then customized with a scripting language. E.g. TCL in openocd.
PyCS is written in Python and customized using Python.

## Customization

There are multiple levels of customixation:

 1. The Cortex-M family.
 2. The specific Cortex-M core. m0, m0plus, m1, m3, m4, m7, interrupts, priority levels, etc.
 3. The vendor chip family. Same core, similar peripherals, different speeds, memories, etc.
 4. The specific vendor chip. Everything that's in a specific part number.
 5. The target board. The chip + external peripherals + gpios + etc.

The idea is to have as much common code as possible.

## Vendor Files

The vendor directory contains the code that takes basic Cortex-M functionality and adds specific vendor features.

 * Specific Coretcx-M core: type, interrupts, priority levels, etc
 * SVD file: to decode the peripheral registers
 * Memory: flash and ram regions
 * Other....

 E.g. ./vendor/nordic/nordic.py

The vendor directory also contains vendor specific drivers.
These are generally for things like gpio or flash access.

## Target Files

The target directory contains <name>.py files where <name> is the name of the target.
The target files specifies which specific chip is being used and also provides target specific customization.
E.g. Details that are specific to that particular target board.

 * gpio naming
 * external devices
 * default debug interface

 E.g. ./target/mb997c.py
