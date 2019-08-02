
# Play the nes game
import asyncio
from enum import Enum
import json
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


class BlackScreen(Enum):
    NotBlack = 0
    JustBlack = 1
    World = 2
    GameOver = 3


screenshot_dir = "./screenshots"

#tensorflow_frozen_graph = "tensorflow/mario-model-frozen-2019-03-10/frozen_inference_graph.pb"
tensorflow_frozen_graph = "tensorflow/mario-model-frozen-2019-07-04/frozen_inference_graph.pb"
#tensorflow_frozen_graph = "tensorflow/mario-model-rcnn-2019-07-08/frozen_inference_graph.pb"
tensorflow_frozen_graph = "tensorflow/mario-model-simple-2019-07-17/frozen_inference_graph.pb"


# The brown block obstacles go from from block_col_1 to block_col_2
obstacle_block_col_1 = [ 240, 208, 176 ]
obstacle_block_col_2 = [ 228, 92, 16 ]
obstacle_block_max_dist = 50   # How many pixels to check in front of mario

# pixels for various words
black_text_words = [
    { 'label': 'world',
      'id' : BlackScreen.World,
      'x1': 88,
      'y1': 80,
      'x2': 126,
      'y2': 86,
      'pix': [[[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [0, 0, 0], [252, 252, 252]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [252, 252, 252]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]] ]
    },

    { 'label': 'game',
      'id' : BlackScreen.GameOver,
      'x1': 88,
      'y1': 128,
      'x2': 118,
      'y2': 134,
      'pix': [[[0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [0, 0, 0]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [252, 252, 252]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [0, 0, 0], [0, 0, 0]],
              [[0, 0, 0], [0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [0, 0, 0]],
              [[0, 0, 0], [252, 252, 252], [252, 252, 252], [252, 252, 252], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0], [0, 0, 0]],
              [[252, 252, 252], [0, 0, 0], [0, 0, 0], [252, 252, 252], [0, 0, 0], [0, 0, 0]]]
      }
    ]

# marker dot = 222, 30
number_pixels = {
    '0': [[None, None, [252, 252, 252], [252, 252, 252], [252, 252, 252], None],
          [None, [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], None, None, None, None, [252, 252, 252]],
          [[252, 252, 252], None, None, None, None, None],
          [[252, 252, 252], [252, 252, 252], None, None, None, None],
          [None, [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]]],

    '1': [[None, None, None, None, None, None],
          [None, None, None, None, None, None],
          [None, [252, 252, 252], None, None, None, None],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [None, None, None, None, None, None]],

    '2': [[None, [252, 252, 252], None, None, None, [252, 252, 252]],
          [[252, 252, 252], [252, 252, 252], None, None, [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], None, None, [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], None, None, [252, 252, 252], [252, 252, 252], None],
          [[252, 252, 252], None, [252, 252, 252], [252, 252, 252], [252, 252, 252], None],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], None, None]],

    '3': [[None, None, None, None, None, [252, 252, 252]],
          [[252, 252, 252], None, None, None, None, [252, 252, 252]],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], None, [252, 252, 252], [252, 252, 252], None, None],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], None, None],
          [[252, 252, 252], [252, 252, 252], None, [252, 252, 252], [252, 252, 252], [252, 252, 252]]],

    '4': [[None, None, None, [252, 252, 252], [252, 252, 252], None],
          [None, None, [252, 252, 252], [252, 252, 252], [252, 252, 252], None],
          [None, [252, 252, 252], [252, 252, 252], None, [252, 252, 252], None],
          [[252, 252, 252], [252, 252, 252], None, None, [252, 252, 252], None],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]]],

    '5': [[None, [252, 252, 252], [252, 252, 252], None, None, [252, 252, 252]],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], None, None, [252, 252, 252]],
          [[252, 252, 252], None, [252, 252, 252], None, None, None],
          [[252, 252, 252], None, [252, 252, 252], None, None, None],
          [[252, 252, 252], None, [252, 252, 252], None, None, None],
          [[252, 252, 252], None, [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]]],

    '6': [[None, None, [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [None, [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], [252, 252, 252], None, [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], [252, 252, 252], [252, 252, 252]]],

    '7': [[None, [252, 252, 252], None, None, None, None],
          [[252, 252, 252], [252, 252, 252], None, None, None, None],
          [[252, 252, 252], None, None, None, [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], None, None, [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], None, [252, 252, 252], [252, 252, 252], None, None],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], None, None, None]],

    '8': [[None, [252, 252, 252], [252, 252, 252], None, [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]]],

    '9': [[None, [252, 252, 252], [252, 252, 252], None, None, None],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], None, None],
          [[252, 252, 252], None, None, [252, 252, 252], None, [252, 252, 252]],
          [[252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252], [252, 252, 252]]],
    }


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

    # Our array needs to be reshaped and then transposed, because otherwise
    # we end up with each line offset (256-240) pixels, and also drawn 90 degrees
    # rotated anti clock wise :(
    screen = pixels_np.reshape((NES_HEIGHT, NES_WIDTH, -1))

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

    # get the pygame surface as a 3d (r,g,b) array
    new_surf = pygame.transform.scale(surface, (256*3, 240*3))
    image = pygame.surfarray.array3d(new_surf)

    output_dict = tf_session.run(tensor_dict, feed_dict={image_tensor: np.expand_dims(image, 0)})

    # all outputs are float32 numpy arrays, so convert types as appropriate
    output_dict['num_detections'] = int(output_dict['num_detections'][0])
    output_dict['detection_classes'] = output_dict[
        'detection_classes'][0].astype(np.uint8)
    output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
    output_dict['detection_scores'] = output_dict['detection_scores'][0]
    if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]

    #print("Num detections: {}".format(output_dict['num_detections']))
    for i in range(0, output_dict['num_detections']):
        obj_id = int(output_dict['detection_classes'][i])
        y = int(output_dict['detection_boxes'][i][0] * NES_HEIGHT)
        x = int(output_dict['detection_boxes'][i][1] * NES_WIDTH)
        y2 = int(output_dict['detection_boxes'][i][2] * NES_HEIGHT)
        x2 = int(output_dict['detection_boxes'][i][3] * NES_WIDTH)

        score = output_dict['detection_scores'][i]

#        print("ID: {},  SCORE: {},  BOX:  {} x {}  to  {} x {}".format(obj_id, score, x, y, x2, y2))

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


def is_black_screen(surface):
    """ Check to see if the display is mainly black. Checks a small number of pixels to
        see if any of them are non-black """

    sample_locs = [[255, 100], [100, 100], [0, 239]]

    pix_arr = pygame.surfarray.pixels3d(surface)

    for p in sample_locs:
        pix = pix_arr[p[0], p[1]]
        pv = pix[0] + pix[1] + pix[2]

        if pv > 0:
            return False

    return True


def check_black_screen_text(surface):
    """ Check to see if the display is black, and if so if any text is displayed """

    rv = BlackScreen.NotBlack

    if is_black_screen(surface):
        rv = BlackScreen.JustBlack  # Default if the screen is black

        pix_arr = pygame.surfarray.pixels3d(surface)

        # Check to see if any of the black text words matxh in our expected positions
        for btw in black_text_words:
            sub_pixels = pix_arr[btw['x1']:btw['x2'], btw['y1']:btw['y2']].tolist()

            if sub_pixels == btw['pix']:
                rv = btw['id']
                break

    return rv


def check_number(pix_arr, loc):
    """ Check to see if a number exists in loc in the pixel array.
        Note, this will not work close to the left or bottom screen edge!
    Returns: number, or None """

    for n_id in number_pixels:
        n = number_pixels[n_id]

        n_width = len(n[0])
        n_height = len(n)

        sub_pixels = pix_arr[loc[0]:loc[0] + n_width, loc[1]:loc[1] + n_height].tolist()

        # Check if the sub_pixels match the pattern in the number_pixels arrays
        match = True
        for r_id in range(0, n_height):
            for c_id in range(0, n_width):
                if number_pixels[n_id][r_id][c_id] is None:
                    # Don't compare Nones
                    continue

                elif number_pixels[n_id][r_id][c_id] == sub_pixels[r_id][c_id]:
                    continue

                else:
                    # No match - break out
                    match = False
                    break
        if match:
            return int(n_id)

    # Nothing found...
    return None


def get_time_remaining(surface):
    """ Check to see if any numbers are present in the time section of the screen """

    # These are the pixel locations where the time numbers start
    sample_locs = [[208, 24], [216, 24], [224, 24]]

    pix_arr = pygame.surfarray.pixels3d(surface)
    numbers_found = ''

    for loc in sample_locs:
        n = check_number(pix_arr, loc)
        if n is not None:
            numbers_found += str(n)

    if numbers_found:
        return int(numbers_found)
    else:
        return None


def detect_holes(surface):
    """ Detect 'holes' that Mario can fall in to (and die).
        Returns list of pairs of holes, where the first element is the beginning
        of the hole in the X axis, and the second value is the the end of the hole
        in the X axis (all in pixels) """
    holes = []
    pix_arr = pygame.surfarray.pixels3d(surface)

    # We only care about the bottom row, and we calculate everything that is blue on
    # the lowest line as a hole.

    lowest_line = pix_arr[:,NES_HEIGHT-1]

    # The colour of 'holes'
    hole_col = np.array([104, 136, 252], dtype=np.uint8)

    # little state machine for picking out the holes
    in_hole = list(lowest_line[0]) == list(hole_col)
    hole_start = 0
    # iterate across all pixels
    for p_idx in range(0, len(lowest_line)):
        p = lowest_line[p_idx]
        if in_hole and list(p) != list(hole_col):
            # transition to out of hole
            holes.append([hole_start, p_idx - 1])
            in_hole = False
        elif (not in_hole) and list(p) == list(hole_col):
            # new hole detected
            hole_start = p_idx
            in_hole = True

    if in_hole:
        # If we end with a hole, we capture the end of the last hole here
        holes.append([hole_start, NES_WIDTH - 1])

    return holes


def check_screen_scroll(surface, moves_to_right, leftmost_pixels):
    """ Check lower portion of leftmost column of pixels. If there is 
        any change to the previously seen values, assume we've moved 
        the screen, and in that case return an increased moves_to_right
        counter. """

    pix_arr = pygame.surfarray.pixels3d(surface)

    # If leftmost_pixels is None, this is the first time we are called.
    if leftmost_pixels is None:
        leftmost_pixels = pix_arr[0, :].copy()

        return (0, leftmost_pixels)

    else:
        new_pixels = pix_arr[0, :].copy()

        for p_idx in range(0, len(new_pixels)):
            if list(new_pixels[p_idx]) != list(leftmost_pixels[p_idx]):
                # Not the same, so we must have moved
                moves_to_right += 1
                break
        return (moves_to_right, new_pixels)


def check_forward_obstacles(surface, mario_pos):
    """ Check if there's a block in front of Mario (to the right only).
        If yes, return the distance in pixels. If no, return NES_WIDTH """

    pix_arr = pygame.surfarray.pixels3d(surface)

    if mario_pos is None:
        return NES_WIDTH

    y_loc = (mario_pos[2] - 10) % NES_HEIGHT
    x_loc = (mario_pos[3] + 10) % NES_WIDTH

#    print("forward_obstacle:   x_loc = {},   y_loc = {}".format(x_loc, y_loc))

    # Check if we see the pattern block_col1, then block_col2, and if so assume we are in front of a block

    in_front_of_block = False
    for p in range(x_loc, (x_loc + obstacle_block_max_dist) % NES_WIDTH):
#        print("  p = {}:   {}".format(p, pix_arr[p, y_loc]))
        if list(pix_arr[p, y_loc]) == obstacle_block_col_1:
            # Check 6 pixels ahead
            next_loc = p + 6
            if next_loc >= NES_WIDTH:
                # Out of the screen
                break

            if list(pix_arr[next_loc, y_loc]) == obstacle_block_col_2:
                # Found a block
                return max(p - x_loc, 0)  # Delta distance between mario and beginning of block

    return NES_WIDTH
#    for p in range(0, NES_WIDTH):
#        pix_arr[p, y_loc] = np.array([0, 255, 0], dtype=np.uint8)


def build_detected_objects_dict(surface, obj_boxes):
    detected_objects = {'mario': [],
                        'goomba': [],
                        'koopa-troopa': [],
                        'pipe': [],
                        'flag': []
                        }
    for b in obj_boxes:
        # Make a dict up with the detected objects
        colour = (0, 255, 25 * b[4])
        obj_id = None

        if b[4] == 1:
            # Mario - only one hopefully
            obj_id = 'mario'
            colour = (255, 0, 0)

        elif b[4] == 2:
            obj_id = 'goomba'
        elif b[4] == 3:
            obj_id = 'koopa-troopa'
        elif b[4] == 4:
            obj_id = 'flag'

        if obj_id:
            detected_objects[obj_id].append({'pos': [b[0], b[1], b[2], b[3]],
                                             'score': b[5]})
            pygame.draw.rect(surface, colour, (b[0], b[1], b[2] - b[0], b[3] - b[1]), 3)
        else:
            pygame.draw.rect(surface, (0, 0, 255), (b[0], b[1], b[2] - b[0], b[3] - b[1]), 3)

    return detected_objects


def get_mid_of_box(pos):
    """ Calculate the middle of a position box """

    return [(pos[2] - pos[0]) / 2 + pos[0],
            (pos[3] - pos[1]) / 2 + pos[1]]


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

    get_new_screen_contents = True
    old_screen_contents = None

    # Indicator dot
    dot_x_y = [0, 0]
    mark_p1 = [0, 0]
    mark_p2 = [0, 0]


    moves_to_right = 0  # Count how many times the leftmost column of pixels has changed
                        # as a proxy for movement towards the right.



    with object_detection_graph.as_default():


        leftmost_pixels = None
        old_mario_pos = None

        tf_session = tf.Session()
        while running:

            if get_new_screen_contents:
                nes_screen_contents = get_nes_screen_binary(sock)
                old_screen_contents = nes_screen_contents
            else:
                nes_screen_contents = old_screen_contents

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
                    if event.key == pygame.K_h:
                        key_states['h'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_j:
                        key_states['j'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_k:
                        key_states['k'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_l:
                        key_states['l'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_y:
                        key_states['y'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_u:
                        key_states['u'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_i:
                        key_states['i'] = event.type == pygame.KEYDOWN
                    if event.key == pygame.K_o:
                        key_states['o'] = event.type == pygame.KEYDOWN

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


            # try to detect objects in nes_surface and draw bounding boxes
            obj_boxes = detect_objects_in_surface(nes_surface, object_detection_graph, image_tensor,
                                                  tensor_dict, tf_session)

            # Categorize the detected objects
            detected_objects = build_detected_objects_dict(nes_surface, obj_boxes)


            # Make the surface point the right way - note if we do this before passing it into the
            # object detection, we get terrible detection accuracy.
            nes_surface = pygame.transform.flip(nes_surface, True, False)

            # Now, rotate it 90 degrees anti-clock-wise
            rotated_surface = pygame.transform.rotate(nes_surface, 90)
            # Reference to the pixel array
            pix_arr = pygame.surfarray.pixels3d(rotated_surface)

            # Move indicator dot
            if key_states.get('h', False):
                new_x = dot_x_y[0] - 1 if dot_x_y[0] > 0 else 0
                dot_x_y = [new_x, dot_x_y[1]]
            elif key_states.get('l', False):
                new_x = dot_x_y[0] + 1 if dot_x_y[0] < 255 else 255
                dot_x_y = [new_x, dot_x_y[1]]
            elif key_states.get('j', False):
                new_y = dot_x_y[1] + 1 if dot_x_y[1] < 240 else 240
                dot_x_y = [dot_x_y[0], new_y]
            elif key_states.get('k', False):
                new_y = dot_x_y[1] - 1 if dot_x_y[1] > 0 else 0
                dot_x_y = [dot_x_y[0], new_y]

            # Stop doing screen updates on 'y'
            if key_states.get('y', False):
                print("Toggling screen updates")
                get_new_screen_contents = False if get_new_screen_contents is True else True

            # Record mark on i
            if key_states.get('i', False):
                mark_p1 = [dot_x_y[0], dot_x_y[1]]
                print("MARK 1: {}".format(mark_p1))
            # Record mark on o
            if key_states.get('o', False):
                mark_p2 = [dot_x_y[0], dot_x_y[1]]
                print("MARK 2: {}".format(mark_p2))

            # Dump subsection of screen as json on u
            if key_states.get('u', False):
                print("Dumping section of screen")

                sub_pixels = pix_arr[mark_p1[0]:mark_p2[0],
                             mark_p1[1]:mark_p2[1]].tolist()
                print(json.dumps(sub_pixels))

                with open('dumpfile.txt', 'a+') as fd:
                    fd.write("{}\n\n".format(json.dumps(sub_pixels)))
                time.sleep(1)


            #########################################################
            # Figure out actual game state (apart from obj detection)
            #########################################################


            # Check if the screen has moved right
            (moves_to_right, leftmost_pixels) = check_screen_scroll(rotated_surface, moves_to_right,
                                                                    leftmost_pixels)

            # Check for game over screens etc
            black_screen_state = check_black_screen_text(rotated_surface)

            # Check how many seconds are left on the clock
            seconds_left = get_time_remaining(rotated_surface)

            if seconds_left is not None:
                print("Sec: {},    moves: {}".format(seconds_left, moves_to_right))


            # Find all holes
            holes = detect_holes(rotated_surface)
            #            print("Holes: {}".format(holes))

            # Get current position of mario
            mario_pos = None
            if len(detected_objects['mario']) > 0:
                mario_pos = detected_objects['mario'][0]['pos']
                old_mario_pos = mario_pos
            else:
                # If we can't find mario, assume he's in the old pos
                mario_pos = old_mario_pos

            if not mario_pos:
                # Can't find mario, and we've never seen him
                mario_pos = [0, 0, 20, 20]   # dummy values

            # Check to see if there are any blocks in front
            forward_obstacle = check_forward_obstacles(rotated_surface, mario_pos)
            #print("Forward obstacle = {}".format(forward_obstacle))

            # Build relative distances to mario of the objects
            mario_mid = get_mid_of_box(mario_pos)

            # Add the non obj detection objects in to the list of detected objects
            rel_holes = []
            for hole in holes:
                rel_holes.append([mario_mid[1] - hole[0], mario_mid[1] - hole[1]])
            #print("Rel holes: {}".format(rel_holes))

            # and now for the tensorflow detected objects
            for obj_id in detected_objects:
                for b in detected_objects[obj_id]:
                    obj_mid = get_mid_of_box(b['pos'])

                    # Rel pos:  negative when object is to the right of mario, and down
                    rel_pos = [ mario_mid[1] - obj_mid[1], mario_mid[0] - obj_mid[0]]

                    b['rel'] = rel_pos

            print("State:   {}".format(detected_objects))

            # Draw indicator dots
            pix_arr[dot_x_y[0], dot_x_y[1]] = [ 0, 255, 0]
            pix_arr[mark_p1[0], mark_p1[1]] = [ 0, 255, 255]
            pix_arr[mark_p2[0], mark_p2[1]] = [ 255, 255, 0]
#            print("marker dot = {}".format(dot_x_y))

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


