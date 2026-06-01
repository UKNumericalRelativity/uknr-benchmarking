#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 </path/to/AMReX_install_dir>" >&2
    exit 1
fi

AMREX_DIR="$1"

patch ${AMREX_DIR}/include/AMReX_Scan.H AMReX_Scan.H.patch