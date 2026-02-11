#!/bin/bash

cd $(dirname "$0")
source ./modules.sh

CODE_DIR=$(realpath ../MHDuet-debug/codes/binary_bh)

cd $CODE_DIR
make clean
make -j 8 CXX=g++
