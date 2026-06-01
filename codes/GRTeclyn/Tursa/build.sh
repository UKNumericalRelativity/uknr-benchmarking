#!/bin/bash

cd $(dirname "$0")
source ./modules.sh

EXAMPLE_DIR=$(realpath ../GRTeclyn/Examples/BinaryBH)

cd $EXAMPLE_DIR

BUILD_ARGS="USE_CUDA=TRUE AMREX_CUDA_ARCH=80 CUDA_LTO=TRUE TINY_PROFILE=TRUE EXTRACXXFLAGS=\"-march=znver2\""

make clean $BUILD_ARGS
make -j 16 $BUILD_ARGS
