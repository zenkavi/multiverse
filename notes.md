
Make sure to set up HPC AWS keys before 

Copy actual data files. This needs to be done *before* you run any of their code

This could be done with something like the code below but `src/download_data.py` has a better way of doing it by unlocking the files.

```python
import shutil
import os

real_path = os.path.realpath("/Users/zenkavi/Documents/EnkaviLab/data/hcp/HCP1200/116726/unprocessed/3T/tfMRI_MOTOR_LR/LINKED_DATA/EPRIME/EVs/t.txt")
destination_dir = "/Users/zenkavi/Documents/EnkaviLab/hcp_multi_pipelines/data/original/MOTOR/116726/unprocessed/3T/tfMRI_MOTOR_LR/LINKED_DATA/EPRIME/EVs/"
shutil.copy(real_path, destination_dir)
```

Start notebook in their docker container

```sh
docker run -it --rm -p 8888:8888 -v /Users/zenkavi/Documents/EnkaviLab/hcp_multi_pipelines:/srv/tempdd/egermani/hcp_pipelines/ --workdir /srv/tempdd/egermani/hcp_pipelines/ elodiegermani/open_pipeline jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

If you've made a mess of a datalad dataset and can't remove the git annex files

```sh
# Make everything writable first, then remove
chmod -R u+w path/to/dataset
rm -rf path/to/dataset
```

11/26/25

- Ran preprocessing, level1 and registration for fsl workflow for one subject through notebook (manually)
- Want to:
    - Run all these steps for 50 subjects on the cluster for the motor and gambling task
    - Run parcellation for a single subject to extract t values
- The first one has more steps and will take some time to run so can play around with the second one once that is running
- What do I need to run all the steps on the cluster
    - ~~hcp_multi_pipelines repo on the cluster~~
    - ~~multiverse repo on the cluster~~
    - ~~data for 50 subjects (structural, motor and gambling). This needs to be downloaded and reorganized~~
        - ~~Download will take time and needs to be scripted~~
        - ~~Organization needs a script~~
    - python script that runs a workflow for a single subject 
        - there is a run_pipeline.py file that might work for this

11/27/25

- Made script to download and organize data
- Moved the two repos onto the cluster
- Testing one subject on cluster worked

```sh
python download_data.py --subjects 116726 --tasks GAMBLING:LR --dataset-path /hopper/groups/enkavilab/data/hcp --output-path /hopper/groups/enkavilab/users/zenkavi/hcp_multi_pipelines/data/original
```

11/29/25

- Realized limits of `download_data.py`. It messes up the datalad structure with `remove_unwanted_directories` and `cleanup_dataset_files`. The correct way to manage disk space using datalad would be `datalad drop` instead of force removing directories I don't want. Can get `download_data.py` to do what I want for the purposes of this project if I ask it to download multiple tasks for each subject before I break te datalad structure. Going to stick with this for now but building a similar workflow in the future should *not* use this approach.
- (Hopefully) done downloading and organizing data on the cluster. 
- Move onto running preprocessing and level1s next.

12/2/25

Test the `run_pipeline.py` locally in Docker container.

Make sure to add `pip install niflow-nipype1-workflows` in the container Python session

```sh
# Do preprocessing for one contrast of MOTOR task for one subject
python run_pipeline.py -e /srv/tempdd/egermani/hcp_pipelines/data/original -r /srv/tempdd/egermani/hcp_pipelines/data/derived -s '["118124"]' -o '["preprocessing"]' -S 'fsl' -t '["MOTOR"]' -c '["rh"]' -f 8 -p 0 -h 'derivatives'

# Do level1 for one contrast of MOTOR task for one subject
python run_pipeline.py -e /srv/tempdd/egermani/hcp_pipelines/data/original -r /srv/tempdd/egermani/hcp_pipelines/data/derived -s '["118124"]' -o '["l1"]' -S 'fsl' -t '["MOTOR"]' -c '["rh"]' -f 8 -p 0 -h 'derivatives'

# Do registration for one contrast of MOTOR task for one subject
python run_pipeline.py -e /srv/tempdd/egermani/hcp_pipelines/data/original -r /srv/tempdd/egermani/hcp_pipelines/data/derived -s '["118124"]' -o '["registration"]' -S 'fsl' -t '["MOTOR"]' -c '["rh"]' -f 8 -p 0 -h 'derivatives'

# Do preprocessing for all contrasts of MOTOR task for one subject
python run_pipeline.py -e /srv/tempdd/egermani/hcp_pipelines/data/original -r /srv/tempdd/egermani/hcp_pipelines/data/derived -s '["118124"]' -o '["preprocessing"]' -S 'fsl' -t '["MOTOR"]' -c '["lf", "rf", "rh", "lh", "t"]' -f 8 -p 0 -h 'derivatives'

# Do all steps for all constrasts of MOTOR task for one subject
python run_pipeline.py -e /srv/tempdd/egermani/hcp_pipelines/data/original -r /srv/tempdd/egermani/hcp_pipelines/data/derived -s '["118124"]' -o '["preprocessing", "l1", "registration"]' -S 'fsl' -t '["MOTOR"]' -c '["lf", "rf", "rh", "lh", "t"]' -f 8 -p 0 -h 'derivatives'
```

Can we run docker containers on the cluster or do I need to run it via singularity? 
`which docker` didn't return any results so instead of digging into that, trying singularity first.

Pulled the docker image. This now works on the cluster for interactive testing.

```sh
singularity exec \
  --bind /hopper/groups/enkavilab/users/zenkavi/hcp_multi_pipelines:/srv/tempdd/egermani/hcp_pipelines/ \
  --pwd /srv/tempdd/egermani/hcp_pipelines/ \
  open_pipeline_latest.sif \
  bash
```

12/4/25

- Added the nipype workflow into run_pipelines to make sure it would be there when a job is submitted to run in the container.