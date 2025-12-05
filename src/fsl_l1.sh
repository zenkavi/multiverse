#!/bin/bash
#SBATCH --job-name=fsl_l1_%A_%a
#SBATCH --output=/hopper/groups/enkavilab/users/zenkavi/.out/fsl_l1_%A_%a.out
#SBATCH --error=/hopper/groups/enkavilab/users/zenkavi/.err/fsl_l1_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=06:00:00
#SBATCH --array=1-1200%100
#SBATCH --mail-user=zenkavi@cmc.edu
#SBATCH --mail-type=FAIL

conda init
conda activate datalad_env

# Get the specific command for this array task
COMMAND=$(sed -n "${SLURM_ARRAY_TASK_ID}p" fsl_l1_tasklist.txt)

# Execute the command
eval $COMMAND