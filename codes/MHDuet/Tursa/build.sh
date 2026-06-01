#!/bin/bash

cd $(dirname "$0")
source ./modules.sh

CODE_DIR=$(realpath ../MHDuet-debug/codes/binary_bh)

export AMREX_MULTIDIM=TRUE
export MHDUET_GPU_ARCH=Ampere

cd $CODE_DIR
make clean
make -j 8 CXX=nvcc
