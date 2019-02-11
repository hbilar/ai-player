#!/bin/bash

progdir=$(dirname $0)

img=$1
shift

tf_graph=/tmp/output_graph.pb
tf_labels=/tmp/output_labels.txt

if [[ -z $img ]]; then 
    echo "Supply filename to label"
else
        python3 $progdir/label_image.py \
           --graph=$tf_graph --labels=$tf_labels \
           --input_layer=Placeholder \
           --output_layer=final_result \
           --image=$img $*
fi
