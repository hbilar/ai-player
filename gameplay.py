""" Gameplay functions for super mario goes in here"""

import math
import numpy as np
import pprint
import json
import player



INFINITY_DIST=1

# From https://towardsdatascience.com/machine-learning-for-beginners-an-introduction-to-neural-networks-d49f22d238f9
def sigmoid(x):
  # Our activation function: f(x) = 1 / (1 + e^(-x))
  return 1 / (1 + np.exp(-x))



# From https://towardsdatascience.com/machine-learning-for-beginners-an-introduction-to-neural-networks-d49f22d238f9
class Neuron:
  def __init__(self, weights, bias, activation):
    self.weights = weights
    self.bias = bias
    self.activation = activation

  def activate(self, inputs):
    # Weight inputs, add bias, then use the activation function

    total = np.dot(self.weights, inputs) + self.bias
    return sigmoid(total)  # FIXME: Always using sigmoid


""" Inputs:

    goomba1_x
    goomba1_y
    goomba2_x
    goomba2_y
    koopa1_x
    koopa1_y
    object1         # x dist to the right
    hole1_x         # hole x centre
    holewidth       # How wide the hole is
    pipe_x          # nearest right pipe
    
"""
neural_net_base_def = {
  'inputs' : [],   # list of 10 values

  'layers': [
    { 'name': 'input',
      'activation': 'sigmoid',
      'num_neurons': 8,

      # as many weights as there are inputs
      'weights': [[0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  [0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  [0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  [0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  [0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  [0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  [0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  [0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ],
                  ],
      # as many biases as there are neurons
      #'bias': [-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8 ],
      'bias': [0, 0, 0, 0, 0, 0, 0, 0 ],
      'neurons': []
    },
    {'name': 'hidden1',
     'activation': 'sigmoid',
     'num_neurons': 6,
     'weights': [
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
                 ],
     'bias': [0, 0, 0, 0, 0, 0 ],
     'neurons': []
     },
    {'name': 'output',
     'activation': 'sigmoid',
     'num_neurons': 5,
     'weights': [
         [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
         [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
         [0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
         [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
         [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
         [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        ],
     'bias': [0, 0, 0, 0, 0 ],
     'neurons': []
     }
  ],
}



def dump_net_to_file(net_def, filename):
    """ Write the neural net to filename (in JSON) """

    print("DUMP TO FILE:\n{}\n".format(net_def))

    with open(filename, "w") as fd:
        line = json.dumps(net_def)
        fd.write("{}\n".format(line))

    print("Wrote neural net to {}".format(filename))


def load_net_from_file(filename):
    """ JSON load the contents of a file, and return the dict.
        Used to load custom neural networks """

    print("Loading neural net from {}".format(filename))
    net = None
    with open(filename, "r") as fd:
        net = json.load(fd)

    print("net = {}".format(pprint.pformat(net)))
    return net


def build_neural_net(net_def):
    """ Return a fully populated neural net def """

    populated_def = net_def.copy()

    for layer in populated_def['layers']:
        for n in range(0, layer['num_neurons']):
            weights = layer['weights'][n]
            bias = layer['bias'][n]

            neuron = Neuron(weights, bias, layer['activation'])
            layer['neurons'].append(neuron)


    return populated_def


def process_layer(layer_def, inputs):
    """ Using the input, activate the layer, and return list of results """

#    print("process_layer:  inputs = {}".format(inputs))
#    print("layer_def = {}".format(layer_def))

    outputs = []
    for n in layer_def['neurons']:
        n_res = n.activate(inputs)

        outputs.append(n_res)

    return outputs


def feed_forward_net(net_def, inputs):
    """ Feed forward some inputs through the net. Returns the index of the element in the final layer
        that has the largest value (so it kind of classifies a bit).
        E.g. if output for the last layer is [ 0.3, 0.1, 0.8, 0.3 ], the function returns 2.
    """

#    print("\n")
#    print("feed forward net: inputs = {}".format(inputs))


    inp = inputs.copy()

    for n in range(0, len(net_def['layers'])):

        outputs = process_layer(net_def['layers'][n], inp)
#        print("feed_forward_net:  inputs = {}, outputs = {}".format(inp, outputs))

        inp = outputs.copy()

#    print("inp = {}".format(inp))
    # Index of largest value
    return np.argmax(inp)


def sorted_objects(detected_objects, keyname):
    """ Sort the 'keyname' objects in detected_objects by relative
        distance to mario (ascending) """

    if detected_objects.get(keyname):
        return sorted(detected_objects[keyname],
                      key=lambda u: math.sqrt(u['norm_pos'][0] ** 2 + u['norm_pos'][1] ** 2))
    else:
        return []


def run_ann(detected_objects, nn):
    """ Produce an action for mario, given the state of the world in terms of
        detected objects """

    goomba1 = None
    goomba2 = None
    koopa1 = None

    object1 = None
    pipe = None
    hole = None

    pipe = None

    inputs = []

    # Find goombas
    sorted_goombas = sorted_objects(detected_objects, 'goomba')
    if len(sorted_goombas) > 0:
        goomba1 = sorted_goombas[0]

        inputs.append(goomba1['norm_pos'][0])
        inputs.append(goomba1['norm_pos'][1])
    else:
        inputs.append(INFINITY_DIST)
        inputs.append(INFINITY_DIST)

    if len(sorted_goombas) > 1:
        goomba2 = sorted_goombas[1]
        inputs.append(goomba2['norm_pos'][0])
        inputs.append(goomba2['norm_pos'][1])
    else:
        inputs.append(INFINITY_DIST)
        inputs.append(INFINITY_DIST)

    # Find koopa troopas
    sorted_koopa = sorted_objects(detected_objects, 'koopa-troopa')
    if len(sorted_koopa) > 0:
        koopa1 = sorted_koopa[0]
        inputs.append(koopa1['norm_pos'][0])
        inputs.append(koopa1['norm_pos'][1])
    else:
        inputs.append(INFINITY_DIST)
        inputs.append(INFINITY_DIST)

    # Find obstacles
    sorted_obstacles = sorted_objects(detected_objects, 'obstacle')
    if len(sorted_obstacles) > 0:
        object1 = sorted_obstacles[0]
        inputs.append(object1['norm_pos'][0])
    else:
        inputs.append(INFINITY_DIST)

    # Find pipes
    sorted_pipes = sorted_objects(detected_objects, 'pipe')
    if len(sorted_pipes) > 0:
        pipe = sorted_pipes[0]
        inputs.append(pipe['norm_pos'][0])
    else:
        inputs.append(INFINITY_DIST)

    # Find holes
    sorted_holes = sorted_objects(detected_objects, 'hole')
    if len(sorted_holes) > 0:
        hole = sorted_holes[0]
        inputs.append(hole['norm_pos'][0])
        inputs.append(hole['width'] / player.NES_WIDTH)
    else:
        inputs.append(INFINITY_DIST)
        inputs.append(0)


#    print("ANN: detected_objects: {}".format(pprint.pformat(detected_objects)))
#    print("ANN:   inputs: {}".format(pprint.pformat(inputs)))


    action = feed_forward_net(nn, inputs)

#    print("ANN:   action: {}".format(action))

    return action