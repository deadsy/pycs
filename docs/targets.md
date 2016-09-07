# Target Support

There are many Cortex-M based platforms in the world.
No single tool supports all of them.
Most debuggers are written in C and then customized with a scripting language. E.g. TCL in openocd.
PyCS is written in Python and customized using Python.

## Customization

There are multiple levels of customization:

 1. Cortex-M Options. M0, M0+, M1, M3, M4, M7, number of interrupts, priority bits, etc.
 2. Vendor Chip Options. cpu core, peripherals, memories, speeds, etc.
 3. Target Board. SoC chip, external peripherals, gpio assignments, etc.

The idea is to have as much common code as possible.

## Vendor Files

The vendor directory contains the code that takes general Cortex-M functionality and customizes it to match the specification of a particular vendor chip.

 * Cortex-M core: core type, number of interrupts, priority levels, fpu, scb, etc
 * SVD file: to provide decode of the peripheral registers
 * Memory: flash and ram regions
 * etc.

 E.g. ./vendor/nordic/nordic.py

The vendor directory also contains vendor specific drivers.
These are generally for things like gpio or flash access.

## Target Files

The target directory contains `<name>.py` files where `<name>` is the name of the target.
The target files specifies which chip is being used and provide target specific customization.

 * gpio naming
 * external devices
 * default debug interface
 * etc.

 E.g. ./target/mb997c.py
 
## Guidelines
 * If it's in the vendor datasheet it belongs in the vendor directory.
 * If it's on the schematic it belongs in the target file.
