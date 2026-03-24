#!/bin/bash

#SBATCH -J mhduet-n128-c4
#SBATCH -p cosma8-milan
#SBATCH -A dp415
#SBATCH -a 1-3
#SBATCH -N 4
#SBATCH --ntasks-per-node 32
#SBATCH --cpus-per-task 4
#SBATCH -t 00:40:00
#SBATCH --hint=nomultithread

source ../modules.sh

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=true

# Assume submission dir is same as script dir
MHDUET_DIR=$(realpath ../../MHDuet-debug)
EXECUTABLE="${MHDUET_DIR}/codes/binary_bh/binary_bh.x"
PAR_FILE="../inputs/GW150914.input"

# Run
time mpiexec --map-by ppr:${SLURM_NTASKS_PER_NODE}:node:pe=${OMP_NUM_THREADS} \
             --bind-to-core --report-bindings $EXECUTABLE ../inputs/$PAR_FILE

# Create symlink to job stdout
ln -sf "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.out" "n${SLURM_NTASKS}c${SLURM_CPUS_PER_TASK}_${SLURM_ARRAY_TASK_ID}.out"
