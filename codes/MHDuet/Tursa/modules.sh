module purge
module load /mnt/lustre/tursafs1/home/y07/shared/tursa-modules/setup-env
module load gcc/12.2.0
module load ucx/1.15.0-gcc12-cuda12

# The following adds modules that have been built in a Spack environment
# The environment spack.yaml and spack.lock can be found in the MHDuet-debug repo
# in the scripts/tursa directory
module use /mnt/lustre/tursafs1/home/dp325/shared/spack/20250805/modules/linux-rhel8-zen2
module load cuda/12.3.0/gcc-12.2.0-5bk3ld7 # Spack-created module for external package
module load openmpi/4.1.5/gcc-12.2.0-dhnhqw4 # Spack-created module for external package
module load hdf5/1.14.5/openmpi-4.1.5-gcc-12.2.0-qcp55kg
module load gsl/2.7.1/gcc-12.2.0-armkktg
module load amrex/24.10/openmpi-4.1.5-gcc-12.2.0-wztjdpr
