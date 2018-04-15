# pycs
Python Based ARM CoreSight Debug and Trace Tools

 * PyCS is a python based JTAG/SWD debugger for ARM chips.
 * Its current focus is systems using Cortex-M ARM CPUs.
 * It reads the SoC SVD files to give full peripheral/register decodes for a wide variety of Cortex-M based chips.

## What do I need?
 * A PC with Python installed [(Host System)](https://github.com/deadsy/pycs/blob/master/docs/host.md)
 * A target system with a Cortex-M ARM cpu [(Targets)](https://github.com/deadsy/pycs/blob/master/docs/targets.md)
 * An SWD debug interface [(Debug Interface)](https://github.com/deadsy/pycs/blob/master/docs/debug_itf.md)

## Installing the tool
  * Run "make" - this will build the ARM disassembler library.
  * Run "./pycs" in the same directory you extracted the code to.
  * If you don't have permissions to access USB devices you can fix that (with a udev rules file) or run with "sudo ./pycs"

## Current Targets

    $ ./pycs -l
    supported targets:
      axoloti       : Axoloti Synth Board (STM32F427xG)
      efm32lg       : EFM32 Leopard Gecko Starter Kit (EFM32LG990F256)
      frdm_k64f     : FRDM-K64F Kinetis Development Board (MK64FN1M0VLL12)
      mb1035b       : STM32F3 Discovery Board (STM32F303xC)
      mb1075b       : STM32F4 Discovery Board (STM32F429xI)
      mb997c        : STM32F4 Discovery Board (STM32F407xx)
      nRF51822      : Adafruit BLE USB dongle (nRF51822)
      nRF52dk       : Nordic nRF52DK Development Board (nRF52832)
      nucleo-l432kc : Nucleo-L432KC (STM32L432KC)
      saml21        : Atmel SAM L21 Xplained Pro Evaluation Board (ATSAML21J18B)
      tepo          : Teenage Engineering Pocket Operator (EFM32LG890F128)

## Using the Tool

    $ ./pycs -t mb997c

    pycs: ARM CoreSight Tool 1.0
    STM32F407xx: compiling ./vendor/st/svd/STM32F40x.svd.gz
    ST-Link usb 0483:3748 serial u"H\xffj\x06PuIU'3\x04\x87"
    target voltage 2.889V

    mb997c*>

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
 * program flash
 * Segger RTT client
 * measure counter frequencies
 * etc. etc.

## Other Documents

 * [HOWTO hookup development boards](https://github.com/deadsy/pycs/blob/master/docs/hookup.md)
