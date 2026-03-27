module purge
module load /mnt/lustre/tursafs1/home/y07/shared/tursa-modules/setup-env
module load gcc/12.2.0
module load ucx/1.15.0-gcc12-cuda12

# The following adds modules that have been built in a Spack environment
# The environment spack.yaml and spack.lock can be found in the spack
# subdirectory
module use /home/dp415/dp415/dc-radi1/spack/20251117/modules/linux-rhel8-zen2
module load cuda/12.3.0/gcc-12.2.0-5bk3ld7 # Spack-created module for external package
module load openmpi/4.1.5/gcc-12.2.0-dhnhqw4 # Spack-created module for external package
module load cmake/3.27.4/gcc-12.2.0-jpsoz3t
module load fftw/3.3.10/openmpi-4.1.5-gcc-12.2.0-gtdyd6q
module load gsl/2.7.1/gcc-12.2.0-knjfi75
module load hdf5/1.14.5/openmpi-4.1.5-gcc-12.2.0-55xnqqg
module load hwloc/2.11.1/gcc-12.2.0-t2a4oqd
module load libjpeg/9f/gcc-12.2.0-wkekuny
module load netlib-lapack/3.11.0/gcc-12.2.0-fvusl6o
module load nsimd/3.0.1/gcc-12.2.0-dw3ajnj
module load yaml-cpp/0.8.0/gcc-12.2.0-kpf32yn
module load xz/5.4.6/gcc-12.2.0-q3bxpwz
module load zlib/1.3.1/gcc-12.2.0-xa55qby
module load amrex/24.10/openmpi-4.1.5-gcc-12.2.0-hrajy6d
module load adios2/2.10.1/openmpi-4.1.5-gcc-12.2.0-grsmolm
module load silo/4.11.1/openmpi-4.1.5-gcc-12.2.0-3ispodj
module load papi/7.1.0/gcc-12.2.0-bnpxq6k