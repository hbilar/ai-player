#!/bin/bash


progdir=$(dirname $0)



if [[ -z $1 ]]; then 
    echo "Supply image directory"
else
    python3 $progdir/retrain.py --image_dir $1
fi
