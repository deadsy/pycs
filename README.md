# pycs
Python Based ARM CoreSight Debug and Trace Tools

# Setup JTAG Device Permissions

 1. Use "lsusb" to get the VID:PID information
```
>lsusb
...
Bus 001 Device 006: ID 0403:cff8 Future Technology Devices International, Ltd Amontec JTAGkey
...
```
 2. Create a file in /etc/udev/rules.d (e.g. 80-jtag.rules) with this information:
```
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="cff8", MODE="0666"
```
 3. Unplug and Re-plug in the USB device to have the changes take effect.
