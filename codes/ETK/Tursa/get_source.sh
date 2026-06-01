#!/bin/bash

cd $(dirname "$0")

# Download GetComponents script
curl -LO https://raw.githubusercontent.com/gridaphobe/CRL/refs/heads/master/GetComponents
chmod +x GetComponents

# Call GetComponents to download the necessary thorns
./GetComponents --root ./Cactus --noshallow ETK-CarpetX-subcycling.th

# We need to check out specific commits for our thorns for consistency
cd Cactus/repos
git -C cactusbase switch --detach 49a9d71
git -C cactusutils switch --detach 474e6b1
git -C CarpetX switch --detach 1664da74
git -C CarpetXUtils switch --detach 4e308b0
git -C ExternalLibraries-ADIOS2 switch --detach
git -C ExternalLibraries-AMReX switch --detach 1cb8dd5
git -C ExternalLibraries-BLAS switch --detach 2da2134
git -C ExternalLibraries-FFTW3 switch --detach 6567c52
git -C ExternalLibraries-GSL switch --detach bca79a9
git -C ExternalLibraries-HDF5 switch --detach 5bde5bf
git -C ExternalLibraries-hwloc switch --detach ddda172
git -C ExternalLibraries-LAPACK switch --detach 90f4f1a
git -C ExternalLibraries-libjpeg switch --detach d5c1c55
git -C ExternalLibraries-MPI switch --detach 8f1b760
git -C ExternalLibraries-NSIMD switch --detach dcbde10
git -C ExternalLibraries-openPMD switch --detach c6ac85d
git -C ExternalLibraries-OpenSSL switch --detach 2c585f3
git -C ExternalLibraries-PAPI switch --detach 6ee7210
git -C ExternalLibraries-pthreads switch --detach 554c0bb
git -C ExternalLibraries-Silo switch --detach b672729
git -C ExternalLibraries-ssht switch --detach 8d465b6
git -C ExternalLibraries-yaml_cpp switch --detach 0a4f089
git -C ExternalLibraries-zlib switch --detach a013c30
git -C flesh switch --detach cb2d7649
git -C numerical switch --detach 535f597
git -C simfactory2 switch --detach 7e397f3d
git -C SpacetimeX switch --detach edddef3e
git -C utilities switch --detach 5b9fc0b