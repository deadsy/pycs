#!/usr/bin/python

import json
from parser import SVDParser

parser = SVDParser.for_xml_file('../../svd/st/STM32F40x.svd')

svd_dict = parser.get_device().to_dict()
print(json.dumps(svd_dict, sort_keys=True,
                 indent=4, separators=(',', ': ')))

#for peripheral in parser.get_device().peripherals:
#    print("%s @ 0x%08x" % (peripheral.name, peripheral.base_address))

