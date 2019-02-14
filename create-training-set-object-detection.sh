#!/bin/bash
# 
# Wrapper to call the create_training_data.py script and generate a bunch
# of training data for the object detection models.


generate_image_script="create_training_data.py"
outdir="training"
types="goomba koopa-troopa mario-small mario-large"

cd $(dirname $0)

for t in $types; do
    echo "type $t"

    # figure out how many different images we have of a specific type
    num_files=$(echo enemies/${t}-*.gif | wc -w)
    how_many=$(expr 50 / $num_files)

    echo "num_files = $num_files"
    echo "how_many = $how_many"

    # generate a bunch of objects on random coloured background
    for f in enemies/${t}-*.gif; do 
        python3 $generate_image_script $f --many=$how_many --outdir=training --label=$t
    done

    # generate a bunch of objects on a set of the empty background images
    how_many_per_background=10
    for f in enemies/${t}-*.gif; do 
        for bg in empty-images/empty-level*.jpg; do
            python3 $generate_image_script $f --background-img=$bg --many=$how_many_per_background --outdir=training --label=$t
        done
    done
    
done
