subjects = ['110613', '111009', '111211', '111312', '111413', '111514', '111716', '112112', '112314', '112516', '112819', '112920', '113215', '113316', '113417', '113619', '113821', '113922', '114116', '114217', '114318', '114419', '114621', '114823', '114924', '115017', '115219', '115320', '115724', '115825', '116221', '116423', '116524', '116726', '117021', '117122', '117324', '117728', '117930', '118023', '118124', '118225', '118528', '118730', '118831', '118932', '119025', '119126', '119732', '119833']
tasks = ["MOTOR:LR,GAMBLING:LR"]

with open('download_data_tasklist.txt', 'w') as f:
    for subject in subjects:
        for task in tasks:
            command = f"python download_data.py --subjects {subject} --tasks {task}:LR --dataset-path /hopper/groups/enkavilab/data/hcp --output-path /hopper/groups/enkavilab/users/zenkavi/hcp_multi_pipelines/data/original\n"
            f.write(command)