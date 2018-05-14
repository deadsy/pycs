#!/bin/bash

LOGFILE="test.log"

rm $LOGFILE
./jlink_test
cat $LOGFILE

