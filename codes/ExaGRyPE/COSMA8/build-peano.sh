#!/bin/bash

cd $(dirname "$0")
source ./modules.sh

PEANO_DIR=$(realpath ../Peano)

cd $PEANO_DIR

# First clean up from any previous configures/builds
git clean -dfx

# From docs
# libtoolize
# aclocal
# autoconf
# autoheader
# cp src/config.h.in .
# automake --add-missing

# Replace above commands with autoreconf
touch config.h.in
autoreconf -i
cp src/config.h.in .

# Configure build
./configure \
    CC=icx \
    CXX=icpx \
    --with-mpi=mpiicpx \
    --with-multithreading=omp \
    CXXFLAGS="-O3 -fp-model=fast -std=c++20 -qopenmp -march=core-avx2 -mtune=core-avx2 -fomit-frame-pointer -Wno-unknown-attributes -Wno-unused-command-line-argument -Wno-vla-cxx-extension" \
    LDFLAGS="-qopenmp" \
    --enable-loadbalancing \
    --enable-exahype \
    --enable-particles \
    --enable-blockstructured \
    --enable-finiteelements

# Build Peano/ExaHyPE
make -j 8

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
