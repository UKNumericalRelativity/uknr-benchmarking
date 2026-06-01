#!/bin/bash

cd $(dirname "$0")
source ./modules.sh

EXAMPLE_DIR=$(realpath ../GRTeclyn/Examples/BinaryBH)

cd $EXAMPLE_DIR

BUILD_ARGS="COMP=intel-llvm USE_OMP=TRUE TINY_PROFILE=TRUE EXTRACXXFLAGS=\"-march=core-avx2\""

make clean $BUILD_ARGS
make -j 8 $BUILD_ARGS
