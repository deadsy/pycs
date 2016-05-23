#!/bin/bash

SVD_FILES=`ls *.svd`

for i in $SVD_FILES; do
  gzip -9 $i
done
