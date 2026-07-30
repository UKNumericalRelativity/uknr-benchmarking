# MHDuet dependency building

We have built the dependencies for MHDuet using [Spack](https://spack.io/).
Instructions on how to build them are provided below

## COSMA8

1. First clone the Spack repository. The [rather old] commit is the version we
   used for testing.
   ```bash
   git clone --depth=2 --revision=9ac261af https://github.com/spack/spack.git
   ```
1. Setup your environment to use Spack:
   ```bash
   source spack/share/spack/setup-env.sh
   ```
1. Create a Spack environment using the [spack.yaml
   file](COSMA8/spack/spack.yaml):
   ```bash
   spack env create mhduet-deps-cosma8 \
       /path/to/uknr-benchmarking/codes/MHDuet/COSMA8/spack/spack.yaml
   ```
1. Activate the Spack environment
   ```bash
   spack env activate mhduet-deps-cosma8
   ```
1. Concretize the environment
   ```bash
   spack concretize -j 2
   ```
1. Build the packages
   ```bash
   spack install -j 8
   ```
1. Module files will be installed under
   ```
   /path/to/spack/../spack-modules-20241030/linux-rhel8-zen2
   ```
   Replace the path passed to `module use` in [modules.sh](COSMA8/modules.sh)
   with the path above.

You should now be able to build the MHDuet code with the
[build.sh](COSMA8/build.sh) script.

## Tursa

The instructions are similar to above but we instead use the system Spack
instance installed under
```
/home/y07/shared/utils/core/spack
```
The [spack.yaml](MHDuet-debug/scripts/tursa/spack.yaml) can be found in the
repository under `scripts/tursa/spack.yaml`. The
[setup.sh](MHDuet-debug/scripts/tursa/setup.sh) script automates building the
dependencies in a shared space for the `PROJECT` defined in
[settings.sh](MHDuet-debug/scripts/tursa/settings.sh).



