#!/bin/bash

#SBATCH -J grteclyn-n32-c4
#SBATCH -p cosma8-milan
#SBATCH -A dp415
#SBATCH -a 1-3
#SBATCH -N 1
#SBATCH --ntasks-per-node 32
#SBATCH --cpus-per-task 4
#SBATCH -t 01:00:00

source ../modules.sh

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=true

export I_MPI_PIN_DOMAIN=omp:compact
export I_MPI_PIN_CELL=core # Ignore SMT

# Assume submission dir is same as script dir
GRTECLYN_DIR=$(realpath ../../GRTeclyn)
EXECUTABLE="${GRTECLYN_DIR}/Examples/BinaryBH/main3d.intel-llvm.TPROF.MPI.OMP.ex"
PAR_FILE="../inputs/params_GW150914.txt"

# Run
time mpiexec $EXECUTABLE $PAR_FILE

# Create symlink to job stdout
ln -sf "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.out" "n${SLURM_NTASKS}c${SLURM_CPUS_PER_TASK}_${SLURM_ARRAY_TASK_ID}.out"
