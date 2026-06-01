# Spack environment for ETK dependencies

This directory contains the Spack environment used to build some of the
dependencies for the ETK on Tursa. It uses the system Spack installation for
which documentation can be found
[here](https://epcced.github.io/dirac-docs/tursa-user-guide/spack/) which is at
version
```
0.23.0.dev0 (c8bebff7f5c5d805decfc340a4ff5791eb90ecc9)
```

## Patch for Tursa-specific issue

Unfortunately there is an issue on Tursa which causes CarpetX to abort with a
CUDA API error. For more details see [this AMReX
discussion](https://github.com/AMReX-Codes/amrex/discussions/4795). To
work around this, there is also a patch in this directory which prevents using
the problematic codepath. The patch can be applied with
[`patch_amrex.sh`](./patch_amrex.sh) as described below.

## Installation instructions

1. First add Spack to your environment by sourcing the environment setup script:
   ```bash
   source /home/y07/shared/utils/core/spack/share/spack/setup-env.sh
   ```
1. Next create a directory for this Spack environment and the packages that
   will be installed in it:
   ```bash
   mkdir -p /path/to/spack/dir/environments
   ```
   Mine was `/home/dp415/dp415/dc-radi1/spack/20251117/environments`. Note that
   packages will be installed under `/path/to/spack/dir/opt` and modules will be
   created under `/path/to/spack/dir/modules`.
1. Create and activate the Spack environment using the
   [`spack.yaml`](./spack.yaml) file in this directory:
   ```bash
   spack env create -d /path/to/spack/dir/environments/<env_name> spack.yaml
   spack env activate /path/to/spack/dir/environments/<env_name>
   ```
   I used `<env_name> = etk-deps-20251117`.
1. Concretize the specs in the Spack environment:
   ```bash
   spack concretize -j 8
   ```
1. Install the concretized specs:
   ```bash
   spack install -j 8
   ```
1. Patch AMReX using the patch described above:
   ```bash
   ./patch_amrex.sh $(spack find -p amrex | tail -n 1 | awk '{print $2}')
   ```
   The command in `$(...)` returns the AMReX installation prefix.


