#!/usr/bin/python

import jlink

def main():

  jtag_driver = jlink.jtag(sn = None)
  print jtag_driver


main()
