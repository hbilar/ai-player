#!/bin/bash

# Split a training, residing in $sourcedir, up into 80% training
# and 20% testing sets, and create the split set in $destdir.
#
# Note, moves the files

sourcedir=/home/henrik/files/project/ai-player/training
destdir=/home/henrik/files/project/models/research/data
train_test_split=8   # 8 10ths of data for testing




for d in $sourcedir/*; do
	dn=$(basename $d)
	echo d = $d
	
	count_jpg=$(ls -1 $d/*.jpg | wc -l)
	count_train=$(( $count_jpg * $train_test_split * 10 / 100 ))

	echo "count = $count_jpg   count_train = $count_train"

	# move training data
	for p in $(ls -1 $d/*.jpg | head -n $count_train); do
		base=$(echo $p | sed -e 's/\.jpg$//')

		if [[ ! -d $destdir/train/$dn ]]; then
			mkdir -p $destdir/train/$dn
		fi
		mv $base.jpg $base.xml $destdir/train/$dn
	done

	# move test data
	if [[ ! -d $destdir/test ]]; then
		mkdir -p $destdir/test
	fi
	mv $d $destdir/test
done
