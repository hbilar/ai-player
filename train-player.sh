#!/bin/bash

# Simple script to train the AI player networks.
#
# Networks are stored in the $net_dir/nn, where nn is the generation of the networks (starting at 0).
# This script finds the last run, and reads the 'scores' file to find out which network in the
# generation performed the best.
#
# Once the best network has been identified, the generate_network.py script is called to generate
# another set of networks a new generation directory. The highest scoring network is also copied
# to the new directory.
#
# After generating the nets, this script plays all the new nets (+ parent) and records their scores. 
#
# Once the networks have been played, the script finds the highest score and generates net networks
# that are played, and so on.
#
# Variables:
# nets_per_base: determine how many networks should be generated for a given generation.
# top_n_nets: use the top_n_nets highest scoring nets as the basis for the next generation
# weigth_jitter: Adjust any weight by a maximum +/- weight_jitter.
# bias_jitter: Adjust any bias by a max +/- bias_jitter.
# mutation_likelihood: The chance that any particular neuron gets mutated
#

# Use the top_n_nets as basis for the next set of nets
top_n_nets=1

# These many nets per base_net
nets_per_base=10

weight_jitter=0.01
bias_jitter=0.01
mutation_likelihood=0.4


# Where the neural nets are stored (or rather, the generational directories)
net_dir="gameplay_neural_nets"


function find_last_gen()
{
	# Find the last generation
	last_gen=$(ls -1 $net_dir | egrep '[0-9]+' | sort -n | tail -n 1)
	
	echo "$last_gen"
}


function die()
{
	# Print error message and exit
	echo "FATAL: $*" > /dev/stderr
	exit 1
}


function generate_new_nets()
{
	last_gen=$1
	next_gen=$2

	# Generate new networks
	cur_net_idx=1
	for net in `cat $net_dir/$last_gen/scores | sort -n -k 2 -t: -r | head -n $top_n_nets`; do 

		net_file=`echo $net | cut -f1 -d:`
		score=`echo $net | cut -f2 -d:`

		mkdir -p $net_dir/$next_gen || die "Failed to mkdir"
	
		echo "nets_per_base = $nets_per_base"	

		for i in `seq 1 $nets_per_base`; do

			python3 generate_network.py --input $net_dir/$last_gen/$net_file \
				--weight-max-jitter=${weight_jitter} \
				--bias-max-jitter=${bias_jitter} \
				--mutation-likelihood=${mutation_likelihood} \
				$net_dir/$next_gen/$cur_net_idx.nn

			cur_net_idx=$(expr $cur_net_idx + 1)
		done

		# Also copy the current base net in, so that we always keep the best
		# performing two nets for the next generation
		cp $net_dir/$last_gen/$net_file $net_dir/$next_gen/grand_father_$net_file
	done
}


function play_one_game()
{
	net=$1

	local net_dir=$(dirname $net)
	local net_basename=$(basename $net)

	python3 player.py oneshot $net | tee $net.play.out


	# get score
	score=$(tail -n 10 $net.play.out | awk ' /Moves to the right/  { print $NF } ')

	echo $net_basename:$score >> $net_dir/scores
}


function play_all_nets()
{
	next_gen=$1

	for n in $net_dir/$next_gen/*.nn; do 

		echo "#####################"
		echo "Playing neural net $n"
		sleep 1
		play_one_game $n
	done
}


# Write settings to neural nets dir 
(
	echo "============================================"
	echo "Starting run at `date`"
	echo "Params:"
	echo "top_n_nets=$top_n_nets"
	echo "nets_per_base=$nets_per_base"
	echo "weight_jitter=$weight_jitter"
	echo "bias_jitter=$bias_jitter"
	echo "mutation_likelihood=$mutation_likelihood"
	echo
) >> $net_dir/train-settings

done=0
while [[ $done -eq 0 ]]; do 

	last_gen=$(find_last_gen)
	next_gen=$(expr $last_gen + 1)

	
	# Find scores in last_gen, and find top_n_nets

	generate_new_nets $last_gen $next_gen

	echo "########################################################"
	echo "last_gen = $last_gen"
	echo "next_gen = $next_gen"
	echo "Nets:"
	ls -l $net_dir/$next_gen/
	sleep 1


	play_all_nets $next_gen
done

