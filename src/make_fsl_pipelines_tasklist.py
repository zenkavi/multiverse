import json

subjects = ['110613', '111009', '111211', '111312', '111413', '111514', '111716', '112112', '112314', '112516', '112819', '112920', '113215', '113316', '113417', '113619', '113821', '113922', '114116', '114217', '114318', '114419', '114621', '114823', '114924', '115017', '115219', '115320', '115724', '115825', '116221', '116423', '116524', '116726', '117021', '117122', '117324', '117728', '117930', '118023', '118124', '118225', '118528', '118730', '118831', '118932', '119025', '119126', '119732', '119833']
tasks = ['MOTOR', 'GAMBLING']
task_contrasts = {'MOTOR': ["lf", "rf", "rh", "lh", "t"], 'GAMBLING': ["loss", "loss_event", "win", "win_event", "neut_event"]}
fwhms = [5, 8]
motions = [0, 6, 24]
hrfs = ['derivatives', 'no_derivatives']

with open('fsl_pipeplines_tasklist.txt', 'w') as f:
    for SUBNUM in subjects:
        for TASK in tasks:
            CONTRASTS = task_contrasts[TASK]
            for FWHM in fwhms:
                for MOTION in motions:
                    for HRF in hrfs:
                        contrasts_str = json.dumps(CONTRASTS)  # This gives you ["item1", "item2", ...]
                        command = f"singularity exec --bind /hopper/groups/enkavilab/users/zenkavi/hcp_multi_pipelines:/srv/tempdd/egermani/hcp_pipelines/ --pwd /srv/tempdd/egermani/hcp_pipelines/src /hopper/groups/enkavilab/singularity_images/open_pipeline_latest.sif python run_pipeline.py -e /srv/tempdd/egermani/hcp_pipelines/data/original -r /srv/tempdd/egermani/hcp_pipelines/data/derived -s '[{SUBNUM}]' -o '[\"preprocessing\", \"l1\", \"registration\"]' -S \"fsl\" -t '[{TASK}]' -c '{contrasts_str}' -f {FWHM} -p {MOTION} -h \"{HRF}\"\n"
                        f.write(command)


