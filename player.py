
# Play the nes game
import asyncio
import pprint
import pygame
import random
import time
import sys
import socket
import numpy as np
import struct
import select
import stat
import os
import datetime

import tensorflow as tf

NES_WIDTH = 256
NES_HEIGHT = 240

screen_size = [3 * NES_WIDTH, 3 * NES_HEIGHT ]

screenshot_dir = "./screenshots"

#tensorflow_frozen_graph = "tensorflow/mario-model-frozen-2019-03-10/frozen_inference_graph.pb"
tensorflow_frozen_graph = "tensorflow/mario-model-frozen-2019-07-04/frozen_inference_graph.pb"
#tensorflow_frozen_graph = "tensorflow/mario-model-rcnn-2019-07-08/frozen_inference_graph.pb"
tensorflow_frozen_graph = "tensorflow/mario-model-simple-2019-07-17/frozen_inference_graph.pb"


def setup_screen():
    pygame.init()
    return pygame.display.set_mode(screen_size)


def draw_nes_screen(screen, nes_screen):
    """ Draw the nes screen buffer to the screen """

    pygame.surfarray.blit_array(screen, nes_screen)


def connect_to_game_server(address, port):
    # type: (str, int) -> socket
    """ Connect to a game server. Returns a socket.

        Raises: ConectionRefusedError
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))

#    sock.setblocking(False)
    return sock


def clear_socket(sock):
    """ Read from socket until there's nothing else to read (i.e. drain it) """

    while True:
        (readable, writable, exceptions) = select.select([sock], [], [], 0)
        if len(readable) > 0:
            # there is data to be read
            data = sock.recv(4096)
            if len(data) <= 0:
                # actually, no there wasn't...
                break
        else:
            # no data to read (a read would block)
            break


def send_to_socket(sock, message):
    # type: (socket, str) -> None
    """ Send the message to the socket. """

    while len(message) > 0:
        bytes_sent = sock.send(message.encode())
        message = message[bytes_sent:]


def get_nes_screen_binary(sock):
    """ Get the latest screen from the NES server using the
        binary protocol (basically just a dump of the screen
        buffer).

        Returns a numpy 3d array of [x][y][r,g,b].
    """

    # send command
    clear_socket(sock)
    send_to_socket(sock, "binscreen\n")

    recvd_bytes = 0
    pixels = bytearray()
    # FIXME: Make this non-blocking (using the same select as in the clear_socket
    while (recvd_bytes < NES_HEIGHT*NES_WIDTH*3):
        # keep looping until full message is received
        data = sock.recv(4096)

        recvd_bytes = recvd_bytes + len(data)
        pixels += data

    # Make the bytearray a numpy array. Also, we sometimes get some
    # extra data back (I blame the \n characters..), so we make sure that
    # the array is the right size as well (otherwise reshape etc fails)
    pixels_np = np.array(pixels, dtype=np.uint8)
    ## HENRIK maybe unneccessary
    ###pixels_np = pixels_np[ : NES_WIDTH * NES_HEIGHT * 3]

    # Our array needs to be reshaped and then transposed, because otherwise
    # we end up with each line offset (256-240) pixels, and also drawn 90 degrees
    # rotated anti clock wise :(
    ###screen = pixels_np.reshape((NES_HEIGHT, NES_WIDTH, -1)).transpose((1,0,2))

    ## HENRIK

    screen = pixels_np.reshape((NES_HEIGHT, NES_WIDTH, -1)).transpose((1, 0, 2))
    screen = pixels_np.reshape((NES_HEIGHT, NES_WIDTH, -1))
    print("PIXELS: {}, screen = {}".format(pixels_np.shape, screen.shape))

    return screen


def get_nes_screen(sock):
    # type: (socket) -> list
    """ Get the latest screen from the NES server.

        FIXME: This should really be non-blocking...

        Returns a numpy 3d array of [x][y][r,g,b] to represent the pixels.
        The size in y is NES_HEIGHT, and NES_WIDTH in x.
    """

    # Send the command to get the remote to send the screen data
    send_to_socket(sock, "screen\n")

    done = False

    # numpy array to hold the nintendo pixels
    screen = np.zeros(shape=(NES_WIDTH, NES_HEIGHT, 3), dtype=np.int32)

    message_parts = []

    while(not done):
        bytes = sock.recv(4096)
        decoded_bytes = bytes.decode()
        if len(bytes) > 0:
            message_parts.append(decoded_bytes)

        # look for the 'e' in "Done" - FIXME: Ugly..
        if decoded_bytes.find('e') > 0:
            done = True

        if bytes == 0:
            done = True

    received_message = "".join(message_parts)

    # The string coming back has \n and spaces in it - lets get rid of them.
    clean_msg = received_message.replace('display:', '').replace('\n', '').replace(' ', '')

    # split the clean_msg on comma
    tokens = clean_msg.split(',')

    # remove the first 'display:' bit.
    # FIXME: should probably check if we actually got valid screen back rather than just dropping
    if tokens[0] == 'display:':
        tokens.pop(0)

    if tokens[-1] == 'message:Done':
        tokens.pop(-1)

    cur_pos = 0
    for y in range(NES_HEIGHT):
        for x in range(NES_WIDTH):
            (r, g, b) = tokens[cur_pos:cur_pos + 3]
            screen[x][y] = (int(r), int(g), int(b))
            cur_pos = cur_pos + 3

    return screen


def send_key_to_emulator(sock, key_state):
    # type: (socket, dict) -> None
    """ Send a new joypad state to the emulator """

    clear_socket(sock)
    send_to_socket(sock, "j {}\n".format(key_state))


def send_reset_to_emulator(sock):
    # type: (socket) -> None
    """ Send a reset to the emulator """

    clear_socket(sock)
    send_to_socket(sock, "reset\n")


def send_poweroff_to_emulator(sock):
    # type: (socket) -> None
    """ Send a poweroff to the emulator """

    clear_socket(sock)
    send_to_socket(sock, "poweroff\n")


def calculate_key_value(key_states):
    # type: (dict) -> int
    """ From the key_states dict, calculate what the status
        byte to send the emulator should be. """

    j = 1 if key_states['a'] else 0
    j = j | (2 if key_states['b'] else 0)
    j = j | (4 if key_states['select'] else 0)
    j = j | (8 if key_states['start'] else 0)
    j = j | (16 if key_states['up'] else 0)
    j = j | (32 if key_states['down'] else 0)
    j = j | (64 if key_states['left'] else 0)
    j = j | (128 if key_states['right'] else 0)

    return j


def take_screenshot(surface, path=screenshot_dir):
    # type: (surface, str) -> None
    """ Save the surface as a screen shot"""

    # create directory if it doesn't exist
    try:
        stat_info = os.stat(path)
    except OSError:
        # failed to stat - path probably does not exist

        try:
            os.mkdir(path)
        except:
            # raise all exceptions here...
            raise

    time_now = datetime.datetime.now()

    screenshot_name = "screenshot-{:04d}-{:02d}-{:02d}-{:02d}{:02d}{:02d}.jpg".format(time_now.year, time_now.month,
                                                              time_now.day, time_now.hour,
                                                              time_now.minute, time_now.second)

    print("Screenshot name = {}".format(screenshot_name))
    pygame.image.save(surface, "{}/{}".format(path, screenshot_name))


def load_tensorflow_graph(path):
    # type: str -> tf.Graph
    """ Load a frozen tensorflow graph at 'path'.
    Note, the original version of this function came from the TensorFlow tutorials at
    https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
    """

    print("load_tensorflow_graph: path = {}".format(path))
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(path, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
    return detection_graph





def detect_objects_in_surface(surface, graph, image_tensor, tensor_dict, tf_session):
    # type: (pygame.Surface, tf.Graph) -> list
    """ Detect objects in the pygame surface.
        This function used a function from object_detection_tutorial

    """

    return_list = []


    ### TRY RESIZING TO 300 PIXELS
    # get the pygame surface as a 3d (r,g,b) array
    new_surf = pygame.transform.scale(surface, (256*3, 240*3))
    image = pygame.surfarray.array3d(new_surf)
#    image = pygame.surfarray.array3d(surface)

    output_dict = tf_session.run(tensor_dict, feed_dict={image_tensor: np.expand_dims(image, 0)})

    # all outputs are float32 numpy arrays, so convert types as appropriate
    output_dict['num_detections'] = int(output_dict['num_detections'][0])
    output_dict['detection_classes'] = output_dict[
        'detection_classes'][0].astype(np.uint8)
    output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
    output_dict['detection_scores'] = output_dict['detection_scores'][0]
    if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]

    #print("")
    #print("Num detections: {}".format(output_dict['num_detections']))
    for i in range(0, output_dict['num_detections']):
        obj_id = int(output_dict['detection_classes'][i])
        y = int(output_dict['detection_boxes'][i][0] * NES_HEIGHT)
        x = int(output_dict['detection_boxes'][i][1] * NES_WIDTH)
        y2 = int(output_dict['detection_boxes'][i][2] * NES_HEIGHT)
        x2 = int(output_dict['detection_boxes'][i][3] * NES_WIDTH)

        score = output_dict['detection_scores'][i]

        print("ID: {},  SCORE: {},  BOX:  {} x {}  to  {} x {}".format(obj_id, score, x, y, x2, y2))

        return_list.append([y, x, y2, x2, obj_id, score])

    return return_list



def setup_tf_detection_vars(graph):
    with graph.as_default():
        # Get handles to input and output tensors
        ops = tf.get_default_graph().get_operations()
        all_tensor_names = {output.name for op in ops for output in op.outputs}
        tensor_dict = {}
        for key in [
            'num_detections', 'detection_boxes', 'detection_scores',
            'detection_classes', 'detection_masks'
        ]:
            tensor_name = key + ':0'
            if tensor_name in all_tensor_names:
                tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                    tensor_name)
        if 'detection_masks' in tensor_dict:
            # The following processing is only for single image
            detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
            detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
            # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
            real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
            detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
            detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
            detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                detection_masks, detection_boxes, image.shape[0], image.shape[1])
            detection_masks_reframed = tf.cast(
                tf.greater(detection_masks_reframed, 0.5), tf.uint8)
            # Follow the convention by adding back the batch dimension
            tensor_dict['detection_masks'] = tf.expand_dims(
                detection_masks_reframed, 0)
        image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

        return (image_tensor, tensor_dict)


def main_loop(screen, sock):
    """ Main game loop """

    # create a surface for the NES
    nes_surface = pygame.Surface((NES_HEIGHT, NES_WIDTH))
    nes_surface.convert()
    nes_surface.fill((0, 0, 128)) # dark blue background

    # Load a frozen tensorflow graph
    object_detection_graph = load_tensorflow_graph(tensorflow_frozen_graph)
    print("object_detection_graph = {}".format(object_detection_graph))

    # Cerate a tf.Session object, so that we don't have to recreate it every time we
    # run inference
    (image_tensor, tensor_dict) = setup_tf_detection_vars(object_detection_graph)

    clock = pygame.time.Clock()
    running = True


    # The possible joypad states
    key_states = { 'up': False,
                   'down': False,
                   'left': False,
                   'right': False,
                   'a': False,
                   'b': False,
                   'start': False,
                   'select': False }
    key_state = 0


    with object_detection_graph.as_default():
        tf_session = tf.Session()
        while running:
            nes_screen_contents = get_nes_screen_binary(sock)
            # make a surface out of the screen contents
            draw_nes_screen(nes_surface, nes_screen_contents)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    send_poweroff_to_emulator(sock)
                    running = False

                # joypad buttons
                if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        key_states['up'] = event.type == pygame.KEYDOWN
                    elif event.key == pygame.K_DOWN:
                        key_states['down'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_LEFT:
                        key_states['left'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_RIGHT:
                        key_states['right'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_a:
                        key_states['a'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_s:   # NOTE   s, not b
                        key_states['b'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_RETURN:
                        key_states['start'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_q:   # Use q for select (because space for screen shot)
                        key_states['select'] = event.type == pygame.KEYDOWN

                # Reset NES
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    send_reset_to_emulator(sock)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # Take screen shot
                    take_screenshot(nes_surface, path=screenshot_dir)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    # kill remote emulator and ourselves
                    send_poweroff_to_emulator(sock)
                    running = False


            # calculate the key state value. If it's different to the previous
            # value, update the emulator
            tmp_key_state = calculate_key_value(key_states)
            if tmp_key_state != key_state:
                # update the emulator
                key_state = tmp_key_state
                send_key_to_emulator(sock, key_state)


            # try to detect objects in nes_surface
            obj_boxes = detect_objects_in_surface(nes_surface, object_detection_graph, image_tensor,
                                                  tensor_dict, tf_session)
            for b in obj_boxes:

                colour = (0, 255, 0)
                if b[4] == 1:
                    colour = (255, 0, 0)
                pygame.draw.rect(nes_surface, colour, (b[0], b[1], b[2]-b[0], b[3]-b[1]), 3)

            # Make the surface point the right way
            nes_surface = pygame.transform.flip(nes_surface, True, False)

            # Now, rotate it 90 degrees anti-clock-wise
            rotated_surface = pygame.transform.rotate(nes_surface, 90)

            # scale and blit to screen
            screen.blit(pygame.transform.scale(rotated_surface, (2*NES_WIDTH, 2*NES_HEIGHT)), (0, 0))
            pygame.display.flip()



if __name__ == "__main__":

    screen = setup_screen()

    sock = None
    for i in range(8005, 8050):
        try:
            sock = connect_to_game_server('localhost', i)
        except ConnectionRefusedError:
            # try next port
            pass


    if sock is None:
        print("Did you forget to start the emulator?")
        sys.exit(0)

    print("socket: {}".format(sock))

    main_loop(screen, sock)


