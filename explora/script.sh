#!/bin/bash

jupyter notebook --generate-config
python ../set_up_jupyter.py $API_KEY $DEMO_API_KEY
jupyter notebook --port=80 --NotebookApp.token=$TOKEN --no-browser --ip=0.0.0.0 --allow-root