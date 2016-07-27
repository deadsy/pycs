#!/bin/bash

ASM2PY=../../../tools/asm2py

rm lib.py

$ASM2PY stm32f4_flash.S >> lib.py

rm *.o
rm *.elf
rm *.bin

