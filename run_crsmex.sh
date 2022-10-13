#!/bin/bash
#/home/antonio/miniconda3/bin/conda init bash

source /home/antonio/miniconda3/etc/profile.d/conda.sh
conda init bash
source /home/antonio/.bashrc && conda activate twitter && /home/antonio/miniconda3/envs/twitter/bin/python /home/antonio/crsmex_online/api_twitter.py
