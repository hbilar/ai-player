#!/bin/bash


export MODEL_BASE=~/files/project/models/research
export MODEL_DIR=data/mario-model
export PIPELINE=data/pipeline.config


cd $MODEL_BASE
python3 object_detection/model_main.py --alsologtostderr --pipeline_config_path=$PIPELINE --model_dir=$MODEL_DIR
