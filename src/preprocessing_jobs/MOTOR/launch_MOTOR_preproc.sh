#!/bin/bash
#SBATCH --job-name=p1_MOTOR_preprocessing
#SBATCH --output=logs/p1_MOTOR_preprocessing_%J.out
#SBATCH --error=logs/p1_MOTOR_preprocessing_%J.err
#SBATCH --time=12:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=16
#SBATCH --mail-user=zenkavi@cmc.edu
#SBATCH --mail-type=FAIL

# Create logs directory if it doesn't exist
mkdir -p logs

main_script=/hopper/groups/enkavilab/users/zenkavi/multiverse/src/preprocessing_jobs/MOTOR/p1_MOTOR_preprocessing.sh


CONTAINER=/hopper/groups/enkavilab/singularity_images/open_pipeline_latest.sif

# Run everything inside the Singularity container
singularity exec \
    --bind /hopper/groups/enkavilab/users/zenkavi/hcp_multi_pipelines:/srv/tempdd/egermani/hcp_pipelines/ \
    $CONTAINER \
    $main_script