#!/bin/bash
#
# Run the tensorflow retrain.py script to train on the images in
# the screenshots directory
#
# I've used https://www.tensorflow.org/hub/tutorials/image_retraining as a reference
# for the retrain.py command parameters, but otherwise it's my own work.

progdir=$(dirname $0)

# Assume that screenshots live in the sub dir screenshots by default.
screenshot_dir=${1-$progdir/screenshots}

# note, the path is kind of hard coded here..
retrain_prog=${progdir}/external/tensorflow/retrain.py

echo "screenshot dir: ${screenshot_dir}"

set -v


# 224px, 100 neurons in the hidden layers
model="--tfhub_module https://tfhub.dev/google/imagenet/mobilenet_v1_100_224/quantops/feature_vector/1"

# 128px, 25 neurons in the hidden layers
#model="--tfhub_module https://tfhub.dev/google/imagenet/mobilenet_v1_025_128/quantops/feature_vector/1"

python3 ${retrain_prog}  --image_dir $screenshot_dir --print_misclassified_test_images  $model
