#!/bin/bash
# 
# Wrapper to call the create_training_data.py script and generate a bunch
# of training data for the object detection models.
#
# Reads gifs from training-sprites/<type>-*.gif, where type is e.g. goomba, 
# 	mario-small, koopa-troopa etc
#
# Writes training data (images with the sprites pasted into) into a directory
# callex training.


generate_image_script="create_training_data.py"
outdir="training"
types="goomba koopa-troopa mario gameover flag"

cd $(dirname $0)

for t in $types; do
    echo "type $t"

    # figure out how many different images we have of a specific type
    num_files=$(echo training-sprites/${t}-*.gif | wc -w)
    how_many=$(expr 50 / $num_files)

    echo "num_files = $num_files"
    echo "how_many = $how_many"

    # generate a bunch of objects on random coloured background
    for f in training-sprites/${t}-*.gif; do 

	echo "F = $f"
        python3 $generate_image_script $f --many=$how_many --outdir=training --label=$t
    done

    # generate a bunch of objects on a set of the empty background images
    how_many_per_background=10
    for f in training-sprites/${t}-*.gif; do 
        for bg in empty-images/empty-level*.jpg; do
            echo "f(empty image) = $f,   bg = $bo"
            python3 $generate_image_script $f --background-img=$bg --many=$how_many_per_background --outdir=training --label=$t
        done
    done
    
done
