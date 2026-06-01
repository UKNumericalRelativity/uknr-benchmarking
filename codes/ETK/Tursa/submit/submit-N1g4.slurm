#!/bin/bash

#SBATCH -J ETK-N1
#SBATCH -p gpu-a100-80
#SBATCH -A dp415
#SBATCH -a 1-3
#SBATCH -N 1
#SBATCH --gres=gpu:4
#SBATCH --ntasks-per-node=48
#SBATCH -t 01:00:00
#SBATCH -q standard

source ../modules.sh

# Assume submission dir is same as script dir
CACTUS_DIR="$(realpath ../Cactus)"
WRAPPER_SCRIPT="gpu_launch.sh" # in PATH from /mnt/lustre/tursafs1/home/y07/shared/tursa-modules/setup-env module
EXECUTABLE="${CACTUS_DIR}/exe/cactus_sim"
OPTIONS="-L 3"
PAR_FILE="$(realpath ../inputs/GW150914.par)"
CPUS_PER_TASK=$(( SLURM_NTASKS_PER_NODE / SLURM_GPUS_ON_NODE ))

# Set up work directory
WORKDIR="../output/N${SLURM_NNODES}g4/${SLURM_ARRAY_TASK_ID}"
mkdir -p $WORKDIR
cd $WORKDIR

# Run
srun --nodes=$SLURM_NNODES --ntasks-per-node=$SLURM_GPUS_ON_NODE \
     --cpus-per-task=$CPUS_PER_TASK --hint=nomultithread \
     --distribution=block:block $WRAPPER_SCRIPT $EXECUTABLE $OPTIONS $PAR_FILE

# Create symlink to job stdout
ln -sf "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.out" \
       "N${SLURM_NNODES}g${SLURM_GPUS_ON_NODE}_${SLURM_ARRAY_TASK_ID}.out"
