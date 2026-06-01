# UKNR Benchmarking

This repository contains/will contain code, scripts and other files relevant to
the benchmarking of Numerical Relativity codes for the CCP-UKNR scoping grant by
Miren Radia.

## Systems

HPC Resources for this benchmarking project have been kindly provided by the
[STFC DiRAC HPC Facility](https://dirac.ac.uk/). In particular:

* [COSMA8](https://cosma.readthedocs.io/en/latest/) ([DiRAC Memory Intensive
  Service](https://dirac.ac.uk/memory-intensive-durham/))
  * CPU-only with each node comprising:
    * 2x AMD Zen2/3 CPUs (64 cores per socket or 128 cores per node)
    * 1TB RAM
    * Non-blocking HDR200 Infiniband interconnect
* [Tursa](https://epcced.github.io/dirac-docs/tursa-user-guide/) ([DiRAC Extreme
  Scaling Service](https://dirac.ac.uk/extreme-scaling-service-edinburgh/))
  * GPU accelerated with each node comprising
    * 2x AMD Zen2/3 CPUs (16/24 cores per socket or 32/48 cores per node)
    * 1TB RAM
    * 4x Nvidia A100 GPUs each with 40/80GB VRAM
    * Non-blocking HDR200 Infiniband interconnect (4 NICs per node)

## Codes

The following codes are being assessed:
* BAM
* [ExaGRyPE](https://hpcsoftware.pages.gitlab.lrz.de/Peano/dc/d1a/applications_exahype2_ExaGRyPE.html)
* [Einstein Toolkit](https://einsteintoolkit.org/)
  * Carpet
  * CarpetX
* [GRTeclyn](https://github.com/GRTLCollaboration/GRTeclyn)
* [MHDuet](http://mhduet.liu.edu/)

## License

The code in this repository is licensed under the [BSD 3-Clause License](LICENSE).