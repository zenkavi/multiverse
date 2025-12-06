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

# Define your parameters
e=/srv/tempdd/egermani/hcp_pipelines/data/original
r=/srv/tempdd/egermani/hcp_pipelines/data/derived
s_values='["110613", "111009", "111211", "111312", "111413", "111514", "111716", "112112", "112314", "112516", "112819", "112920", "113215", "113316", "113417", "113619", "113821", "113922", "114116", "114217", "114318", "114419", "114621", "114823", "114924", "115017", "115219", "115320", "115724", "115825", "116221", "116423", "116524", "116726", "117021", "117122", "117324", "117728", "117930", "118023", "118124", "118225", "118528", "118730", "118831", "118932", "119025", "119126", "119732", "119833"]'
o='["preprocessing"]'
S='fsl'
t='["MOTOR"]'
c='["rh","rf","lh","lf","t"]'
hrf='derivatives'
p=0
f=5

# main_script=/hopper/groups/enkavilab/users/zenkavi/hcp_multi_pipelines/src/run_pipeline.py
main_script=/srv/tempdd/egermani/hcp_pipelines/src/run_pipeline.py

# Path to Singularity container
CONTAINER=/hopper/groups/enkavilab/singularity_images/open_pipeline_latest.sif

# Get which subject to run
# s_values need to be parsed as an array for this to work, the above string wouldn't work directly
# s=${s_values[$SLURM_ARRAY_TASK_ID]}

# Run everything inside the Singularity container
singularity exec \
    --bind /hopper/groups/enkavilab/users/zenkavi/hcp_multi_pipelines:/srv/tempdd/egermani/hcp_pipelines/ \
    $CONTAINER \
    bash -c "
        source /opt/miniconda-latest/etc/profile.d/conda.sh
        source /opt/miniconda-latest/bin/activate
        conda activate neuro
        python3 $main_script -e $e -r $r -s '$s' -o '$o' -S $S -t '$t' -c '$c' -f $f -p $p -h $hrf
    "