#!/bin/bash

ASM2PY=../../../tools/asm2py
LIB=../lib.py

rm $LIB

$ASM2PY stm32f4_flash.S >> $LIB
$ASM2PY stm32f3_flash.S >> $LIB
