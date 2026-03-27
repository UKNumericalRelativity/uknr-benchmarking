#!/bin/bash

#SBATCH -J ETK-n512-c4
#SBATCH -p cosma8-milan
#SBATCH -A dp415
#SBATCH -a 1-3
#SBATCH -N 16
#SBATCH --ntasks-per-node 32
#SBATCH --cpus-per-task 4
#SBATCH -t 00:10:00

source ../modules.sh

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=true

export I_MPI_PIN_DOMAIN=omp:compact
export I_MPI_PIN_CELL=core # Ignore SMT

# Assume submission dir is same as script dir
CACTUS_DIR="$(realpath ../Cactus)"
EXECUTABLE="${CACTUS_DIR}/exe/cactus_sim"
OPTIONS="-L 3"
PAR_FILE="$(realpath ../inputs/GW150914.par)"

# Set up work directory
WORKDIR="/snap8/scratch/dp415/dc-radi1/ETK/n${SLURM_NTASKS}c${SLURM_CPUS_PER_TASK}/${SLURM_ARRAY_TASK_ID}"
mkdir -p $WORKDIR
cd $WORKDIR

# Run
time mpiexec $EXECUTABLE $OPTIONS $PAR_FILE

# Create symlink to job stdout
cd -
ln -sf "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.out" "n${SLURM_NTASKS}c${SLURM_CPUS_PER_TASK}_${SLURM_ARRAY_TASK_ID}.out"
