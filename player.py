
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


NES_WIDTH = 256
NES_HEIGHT = 240

screen_size = [500, 500]


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
    pixels_np = pixels_np[ : NES_WIDTH * NES_HEIGHT * 3]

    # Our array needs to be reshaped and then transposed, because otherwise
    # we end up with each line offset (256-240) pixels, and also drawn 90 degrees
    # rotated anti clock wise :(
    screen = pixels_np.reshape((NES_HEIGHT, NES_WIDTH, -1)).transpose((1,0,2))

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


def main_loop(screen, sock):
    """ Main game loop """

    # create a surface for the NES
    nes_surface = pygame.Surface((NES_WIDTH, NES_HEIGHT))
    nes_surface.convert()
    nes_surface.fill((0, 0, 128))

#    clock = pygame.time.Clock()
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

    while running:
        nes_screen_contents = get_nes_screen_binary(sock)
        draw_nes_screen(nes_surface, nes_screen_contents)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
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
                if event.key == pygame.K_SPACE:
                    key_states['select'] = event.type == pygame.KEYDOWN

            # reset NES
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                send_reset_to_emulator(sock)

        # calculate the key state value. If it's different to the previous
        # value, update the emulator
        tmp_key_state = calculate_key_value(key_states)
        if tmp_key_state != key_state:
            # update the emulator
            key_state = tmp_key_state
            send_key_to_emulator(sock, key_state)

        # draw the nes surface onto the actual screen
        screen.blit(nes_surface, (200, 20))
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


