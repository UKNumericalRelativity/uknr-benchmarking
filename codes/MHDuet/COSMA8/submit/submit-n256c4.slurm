#!/bin/bash

#SBATCH -J mhduet-n256-c4
#SBATCH -p cosma8-milan
#SBATCH -A dp415
#SBATCH -a 1-3
#SBATCH -N 8
#SBATCH --ntasks-per-node 32
#SBATCH --cpus-per-task 4
#SBATCH -t 01:30:00

source ../modules.sh

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=true

# Assume submission dir is same as script dir
MHDUET_DIR=$(realpath ../../MHDuet-debug)
EXECUTABLE="${MHDUET_DIR}/codes/binary_bh/binary_bh.x"
PAR_FILE="GW150914.input"

# Set up work directory
WORKDIR_PREFIX="/snap8/scratch/dp415/dc-radi1/MHDuet"
SUBDIR="n${SLURM_NTASKS}c${SLURM_CPUS_PER_TASK}/${SLURM_ARRAY_TASK_ID}"
WORKDIR="${WORKDIR_PREFIX}/${SUBDIR}"
mkdir -p $WORKDIR
cp ../inputs/* ${WORKDIR}/

# Run
cd $WORKDIR
time mpiexec $EXECUTABLE $PAR_FILE

# Create symlink to job stdout
ln -sf "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.out" "n${SLURM_NTASKS}c${SLURM_CPUS_PER_TASK}_${SLURM_ARRAY_TASK_ID}.out"
