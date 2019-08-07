#!/usr/bin/bash

# the path to your conda env
PATH_TO_ENV=/tmp/

# your email
EMAIL=me@domain.com

# You may need to source conda.sh for all the conda
# Env vars to be set in the crontab run.
# Find the correct location of this script on your environment
# . /absolute/path/to/your/conda.sh

# You should create your conda with prefix
# $ conda create --prefix /abs/path/envname python
# Then you can download the dependencies and activate as below
conda activate $PATH_TO_ENV
python tweets.py  | mail -s "Twitter Digest" $EMAIL
conda deactivate

