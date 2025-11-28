
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

11/26/25

- Ran preprocessing, level1 and registration for fsl workflow for one subject through notebook (manually)
- Want to:
    - Run all these steps for 50 subjects on the cluster for the motor and gambling task
    - Run parcellation for a single subject to extract t values
- The first one has more steps and will take some time to run so can play around with the second one once that is running
- What do I need to run all the steps on the cluster
    - hcp_multi_pipelines repo on the cluster
    - multiverse repo on the cluster
    - data for 50 subjects (structural, motor and gambling). This needs to be downloaded and reorganized
        - ~~Download will take time and needs to be scripted~~
        - ~~Organization needs a script~~
    - python script that runs a workflow for a single subject 
        - there is a run_pipeline.py file that might work for this

11/27/25

- Made script to download and organize data