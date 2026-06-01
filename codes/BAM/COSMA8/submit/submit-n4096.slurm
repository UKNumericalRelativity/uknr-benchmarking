#!/bin/bash

#SBATCH -J bam-n4096
#SBATCH -p cosma8-milan
#SBATCH -A dp415
#SBATCH -a 1-3
#SBATCH -N 32
#SBATCH --ntasks-per-node 128
#SBATCH -t 00:30:00

source ../modules.sh

# Assume submission dir is same as script dir
BAM_DIR=$(realpath ../../bam-private)
EXECUTABLE="${BAM_DIR}/exe/bamFD6"
PAR_BASENAME="GW150914"
PAR_FILE="${PAR_BASENAME}.par"

# BAM libraries
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$BAM_DIR/lib

# Set up work directory
WORKDIR_PREFIX="/snap8/scratch/dp415/dc-radi1/BAM"
SUBDIR="n${SLURM_NTASKS}/${SLURM_ARRAY_TASK_ID}"
WORKDIR="${WORKDIR_PREFIX}/${SUBDIR}"
mkdir -p $WORKDIR
cp ../inputs/* ${WORKDIR}/

# Run
cd $WORKDIR
time mpiexec $EXECUTABLE $PAR_FILE

# Copy output data back
cd -
OUTPUT_DIR="../outputs/${SUBDIR}"
mkdir -p $OUTPUT_DIR
cp -a ${WORKDIR}/${PAR_BASENAME}/* $OUTPUT_DIR/

# Create symlink to job stdout
ln -sf "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.out" "n${SLURM_NTASKS}_${SLURM_ARRAY_TASK_ID}.out"
