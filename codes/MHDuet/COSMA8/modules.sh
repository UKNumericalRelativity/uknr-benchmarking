module purge
module load gnu_comp/14.1.0

# The following adds modules that have been built in a Spack environment
# The environment spack.yaml and spack.lock can be found in the spack directory
module use /cosma8/data/dp325/dc-radi1/shared/spack-modules-20241030/linux-rocky9-zen2
module load hdf5/1.14.4/gcc-14.1.0-pfyx6hu
module load openmpi/5.0.3/gcc-14.1.0-ks44trh
module load amrex/24.10/openmpi-5.0.3-gcc-14.1.0-pxsj625
