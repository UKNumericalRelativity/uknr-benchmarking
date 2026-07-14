#!/bin/bash

# Assume we have already built Peano with build-peano.sh

cd $(dirname "$0")
source ./modules.sh

PEANO_DIR=$(realpath ../Peano)
EXAGRYPE_DIR=$PEANO_DIR/applications/exahype2/ccz4
cd $PEANO_DIR

# Load Python environment
source .venv/bin/activate
export PYTHONPATH=$PEANO_DIR/python:$EXAGRYPE_DIR

cd $EXAGRYPE_DIR

# Build executable with parameters from docs
python3 ccz4.py \
    -impl fd4-rk1-dsl \
    -s two-punctures \
    -maxh 0.4 \
    -minh 0.04 \
    -ps 8 \
    -plt 0.5 \
    -et 120 \
    -exn bbh \
    --domain_r 12.0 \
    --ReSwi 6 \
    -cfl 0.1 \
    -outdir /snap8/scratch/dp415/$USER/ExaGRyPE/BBH \
    --KOSigma 8.0 \
    --BBHType 2 \
    -sommerfeld \
    -so \
    -ext adm \
    -interp second_order \
    -restrict second_order

