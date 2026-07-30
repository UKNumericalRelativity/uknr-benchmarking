# UKNR Benchmarking

This repository contains code, scripts and other files relevant to the
benchmarking of Numerical Relativity codes for the CCP-UKNR scoping grant by
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

On both systems, we performed a strong scaling test for each code from 1 to 32
nodes. In addition we enabled each code's internal profile/timing output for all
runs.

## Codes

The following codes were assessed:
* BAM[^cosma8-only]
* [ExaGRyPE](https://hpcsoftware.pages.gitlab.lrz.de/Peano/dc/d1a/applications_exahype2_ExaGRyPE.html)[^no-scaling]
* [Einstein Toolkit](https://einsteintoolkit.org/)
  * Carpet[^cosma8-only]
  * CarpetX[^tursa-only]
* [GRTeclyn](https://github.com/GRTLCollaboration/GRTeclyn)
* [MHDuet](http://mhduet.liu.edu/)

## Simulation configuration

For all of the codes we performed strong scaling tests, the simulation
configuration was created using the following procedure:

1. Start with a typical production-size configuration using initial data based
   on the GW150914 LIGO event. This typically has:
   * A domain that has side length $L \geq 1000M$ where $M$ is the total black
     hole mass.
   * The grid spacing on the finest level $\Delta x_{\text{finest}} \leq M/80$.
   * 10-12 levels of mesh refinement.
   * For moving-box style refinement, see, for example, the parameters used for
     the ETK COSMA8 configurations:
     [GW150914.par](codes/ETK/COSMA8/inputs/GW150914.par).
   * Bitant symmetry if available.
2. Disable any unnecessary I/O and analysis such as:
   * Apparent horizon finding
   * $\Psi_4$ and multipole calculations
   * Constraint violation calculations
   * Checkpointing
   Keep puncture tracking enabled as it is often used for mesh refinement
   criterion.
3. Set the end time/termination criterion to be either 1 or 2 timesteps on the
   coarsest level and enable subcycling (for at least some of the levels).
4. Test this configuration by submitting a single node job (use all available
   cores/GPUs on that node) to the relevant partition and monitor the RAM/GPU
   memory used. This can be done by
   * SSHing to the compute node during job execution and running
     `watch -n 1 free -h` (for RAM) or `watch -n 1 nvidia-smi` (for GPU memory).
   * Using SLURM's `seff` command (for RAM).
5. Iterate on the grid spacing/resolution until a configuration is obtained that
   fills most of the available RAM/total GPU memory on a single node. This is
   usually in the range $M/128 \geq \Delta x_{\text{finest}} \geq M/160$.
> [!IMPORTANT]
> For configurations that will be used on both Tursa and COSMA8, since the
> total GPU memory on Tursa (4×80GB = 320GB) is smaller than the total RAM on
> COSMA8 (1TB), do this step on Tursa rather than COSMA8.

## Repository structure

The repository has the following structure:

```
uknr-benchmarking
├── codes
│   ├── <code>
│   │   ├── [<source code repository submodule>] (excluding ETK)
│   │   ├── COSMA8
│   │   │   ├── inputs
│   │   │   │   └── <parameter file>
│   │   │   ├── submit
│   │   │   │   ├── <SLURM job submission scripts>
│   │   │   │   ├── ...
│   │   │   │   ├── <SLURM job stdouts>
│   │   │   │   └── ...
│   │   │   ├── build.sh
│   │   │   ├── modules.sh
│   │   └── [Tursa] (for GPU-enabled codes)
│   │   │   └── <similar to COSMA8>
│   ├── ...
├── ...
└── scripts
    ├── <plotting and profiling scripts>
```

## Instructions

Here are the steps used to build the codes and submit the jobs for the scaling
tests:

1. SSH to either Tursa or COSMA8.
1. Clone this repository including submodules:
   ```bash
   git clone --recurse-submodules https://github.com/UKNumericalRelativity/uknr-benchmarking
   ```
  > [!NOTE]
  > The repositories for MHDuet and BAM are private so it is not possible to
  > reproduce these without access. Please contact the following to request
  > access:
  > * BAM: Mark Hannam, Cardiff University
  > * MHDuet: Miguel Bezares, University of Nottingham
3. Change into the relevant code and system directory:
   ```bash
   cd uknr-benchmarking/codes/<code>/<system>
   ```
1. For ETK only, execute the `get_source.sh` script:
   ```bash
   ./get_source.sh
   ```
1. For MHDuet, it is necessary to build the dependencies. See its separate
   [README](codes/MHDuet/README.md).
1. Execute the `build.sh` script (which will load appropriate modules using the
   `modules.sh` script):
   ```bash
   ./build.sh
   ```
1. Change into the `submit` subdirectory
1. Submit one of the job submission scripts to the queue.  You will need to
   change the allocation account used:
   ```bash
   sbatch --account=<my allocation> submit-<config>.slurm
   ```
> [!NOTE]
> Each script (except for ExaGRyPE) is an array of 3 identical jobs.

The jobs stdout/stderr will be written to the usual `slurm-<jobid>.out` file
in the `submit` subdirectory and then a symbolic link to it will be created
of the form `<job config>_<array index>.out`. The job configs are in one of
the form:
* `n<num MPI processes>` for pure MPI jobs e.g. `n512`
* `n<num MPI proccesses>c<num OpenMP threads>` for hybrid MPI/OpenMP jobs
  e.g. `n128c4`
* `N<num nodes>g<num GPUs per node>` for GPU-accelerated configs e.g. `N4g4`

## Scripts

Both scripts require `matplotlib`. If it's not available in your system Python
installation, you can create a virtual environment and install it there using
your favourite Python environment/package manager. For example

```bash
python3 -m venv matplotlib-venv
source matplotlib-venv/bin/activate
pip install matplotlib
```

### Strong scaling

To see how to use this script, execute

```bash
python3 plot_strong_scaling.py --help
```

### Profiling

To plot the profiling comparisons:

1. Call the `get_<code>[_<system>]_profile.py` script with the job configs
   described at the end of [Instructions section](#instructions) as the only
   argument e.g.
   ```bash
   python3 get_grteclyn_profile.py N4g4
   ```
   or
   ```bash
   python3 get_bam_cosma8_prfile.py n512
   ```
   This will generate a file of the form
   `<code_name>_<system>_<config>_profile_summary.dat`
2. Repeat for all of the codes you wish to include in the plot.
3. Pass the profile summary files to the `plot_profile_comparison.py` e.g.
   ```bash
   python3 plot_profile_comparison.py \
      grteclyn_tursa_N4g4_profile_summary.dat \
      bam_cosma8_n512_profile_summary.dat
   ```


## License

The code in this repository is licensed under the [BSD 3-Clause
License](LICENSE).

[^cosma8-only]: We only ran this code on COSMA8.
[^tursa-only]: We only ran this code on Tursa.
[^no-scaling]: We did not perform a scaling analysis for ExaGRyPE but build and
    job submission instructions are provided for completeness.