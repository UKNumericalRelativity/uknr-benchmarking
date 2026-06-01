#!/bin/bash

#SBATCH -J grteclyn-N32
#SBATCH -p gpu-a100-80
#SBATCH -A dp415
#SBATCH -a 1-3
#SBATCH -N 32
#SBATCH --gres=gpu:4
#SBATCH --ntasks-per-node=48
#SBATCH -t 00:05:00
#SBATCH -q standard

source ../modules.sh

# Assume submission dir is same as script dir
GRTECLYN_DIR=$(realpath ../../GRTeclyn)
WRAPPER_SCRIPT="gpu_launch.sh" # in PATH from /mnt/lustre/tursafs1/home/y07/shared/tursa-modules/setup-env module
EXECUTABLE="${GRTECLYN_DIR}/Examples/BinaryBH/main3d.gnu.TPROF.MPI.CUDA.ex"
PAR_FILE="../inputs/params_GW150914.txt"
CPUS_PER_TASK=$(( SLURM_NTASKS_PER_NODE / SLURM_GPUS_ON_NODE ))

# Run
srun --nodes=$SLURM_NNODES --ntasks-per-node=$SLURM_GPUS_ON_NODE \
     --cpus-per-task=$CPUS_PER_TASK --hint=nomultithread \
     --distribution=block:block $WRAPPER_SCRIPT $EXECUTABLE $PAR_FILE

# Create symlink to job stdout
ln -sf "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.out" "N${SLURM_NNODES}g${SLURM_GPUS_ON_NODE}_${SLURM_ARRAY_TASK_ID}.out"
