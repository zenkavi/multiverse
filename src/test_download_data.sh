#!/bin/bash
#SBATCH --job-name=test_download_hcp_%A_%a
#SBATCH --output=/hopper/groups/enkavilab/users/zenkavi/.out/test_download_%A_%a.out
#SBATCH --error=/hopper/groups/enkavilab/users/zenkavi/.err/test_download_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --array=1-2%2
#SBATCH --mail-user=zenkavi@cmc.edu
#SBATCH --mail-type=FAIL

conda activate datalad_env

# Get the specific command for this array task
COMMAND=$(sed -n "${SLURM_ARRAY_TASK_ID}p" test_data_tasklist.txt)

# Execute the command
eval $COMMAND