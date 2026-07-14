#!/bin/bash

#SBATCH -J exagrype-n2-c128
#SBATCH -p cosma8-milan
#SBATCH -A dp415
#SBATCH -N 2
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 128
#SBATCH -t 04:00:00

source ../modules.sh

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=true

export I_MPI_PIN_DOMAIN=omp:compact
export I_MPI_PIN_CELL=core # Ignore SMT

# Assume submission dir is same as script dir
EXAGRYPE_DIR=$(realpath ../../Peano/applications/exahype2/ccz4)
EXECUTABLE="${EXAGRYPE_DIR}/peano4_bbh"

# Run
time mpiexec $EXECUTABLE
