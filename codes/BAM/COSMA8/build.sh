#!/bin/bash

cd $(dirname "$0")
source ./modules.sh
export USE_MATHEMATICA=FALSE

CODE_DIR=$(realpath ../bam-private)
cp MyConfig $CODE_DIR/

cd $CODE_DIR
make clean
mkdir exe
make -j 8
