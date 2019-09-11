
""" This program generates a new network, using another network as a base. """


import click
import pprint
import random

import gameplay


def mutate_net(net, max_weight_jitter, max_bias_jitter, mutation_rate):
    """ Modify a neural net by adding random jitter to it.
        The jitter added is -max_jitter to +max_jitter, and
        the likelihood of mutation occuring per weight and bias is given
        by mutation rate"""

    new_net = net.copy()

    for n in range(0, len(new_net['layers'])):
        layer = new_net['layers'][n]

        # Add jitter to the weights in the net
        for w1 in layer['weights']:
            for w2_idx in range(0, len(w1)):
                r = random.uniform(0, 1)
                if r < mutation_rate:
                    w1[w2_idx] += random.uniform(-max_weight_jitter, max_weight_jitter)

        # Add jitter to the biases
        for b_idx in range(0, len(layer['bias'])):
            r = random.uniform(0, 1)
            if r < mutation_rate:
                layer['bias'][b_idx] += random.uniform(-max_bias_jitter, max_bias_jitter)

    return new_net


@click.command()
@click.option('--input', help="Use this network as a base, otherwise use built in base def")
@click.option('--weight-max-jitter', default=0.05, help="What's the maximum amount the weights will be adjusted")
@click.option('--bias-max-jitter', default=0.0, help="What's the maximum amount the bias will be adjusted")
@click.option('--mutation-likelihood', default=0.05, help="How likely is a given weight to change")
@click.argument('output')
def handle_cmdline(input, weight_max_jitter, bias_max_jitter, mutation_likelihood, output):

    print("input = {},   output = {}".format(input, output))

    if input:
        input_net = gameplay.load_net_from_file(input)
    else:
        input_net = gameplay.neural_net_base_def


    new_net = mutate_net(input_net, weight_max_jitter, bias_max_jitter, mutation_likelihood)

    new_net['generation'] += 1


    if output is not "":
        gameplay.dump_net_to_file(new_net, output)



if __name__ == "__main__":
    handle_cmdline()

