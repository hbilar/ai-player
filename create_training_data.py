#
# Little utility program that allows you to place an object (i.e. an
# enemy or mario etc) on a background in some location, and also generates
# the coordinate file that the training process needs.


import pygame
import click
import time
import random
import os
import datetime
import pathlib

NES_WIDTH = 256
NES_HEIGHT = 240


def get_bg_surface(background_cols):
    """ Generate a background surface as per the command line params """
    # Create a surface to work with
    bg_surface = pygame.Surface((NES_WIDTH, NES_HEIGHT))
    bg_surface.convert()

    # set background image as defined in the background-cols parameter
    colours = background_cols.split(',')

    if colours[0] == "None":
        # generate random numbers
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
    else:
        r = int(colours[0])
        g = int(colours[1])
        b = int(colours[2])
    bg_surface.fill((r, g, b))

    return bg_surface


def get_xy(object_loc, img_size):
    """ Get an X/Y location for the object (generate one if not specified in object_loc) """

    (obj_x, obj_y) = (None, None)

    if object_loc is not None:
        # specified on the command line
        (obj_x, obj_y) = object_loc.split(',')
        obj_x = int(obj_x)
        obj_y = int(obj_y)

    # location wasn't specified
    if obj_x is None or obj_y is None:
        obj_x = random.randint(0, NES_WIDTH - img_size[0])
        obj_y = random.randint(0, NES_HEIGHT - img_size[1])

    return (obj_x, obj_y)


def get_image(img_path):
    """ Load and return an image if the parameter is not None """

    if img_path is not None:
        img = pygame.image.load(img_path)
        return (img, img.get_rect().size)
    else:
        return (None, (0, 0))


def create_path_if_not_exist(path):
    """ Create a directory "path", if it doesn't already exist """
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def generate_label_file(screenshot_name, label, object_img, obj_x, obj_y, scale):
    """ Generate the training annotation xml file.
        Yes, this function should use the xml libraries.
        FIXME: Use XML libraries instead.
        FIXME: don't assume background image size
        FIXME: Don't assume that file ending is the last three characters (?) """

    basename = os.path.basename(screenshot_name)

    obj_size = object_img.get_rect().size

    xml_filename = screenshot_name[:-4] + ".xml"

    annotation_string = """
        <annotation>
            <folder>{}</folder>
            <filename>{}</filename>
            <path>{}</path>
            <source>
                <database>Unknown</database>
            </source>
            <size>
                <width>{}</width>
                <height>{}</height>
                <depth>3</depth>
            </size>
            <segmented>0</segmented>
            <object>
                <name>{}</name>
                <pose>Unspecified</pose>
                <truncated>0</truncated>
                <difficult>0</difficult>
                <bndbox>
                    <xmin>{}</xmin>
                    <ymin>{}</ymin>
                    <xmax>{}</xmax>
                    <ymax>{}</ymax>
                </bndbox>
            </object>
        </annotation>
    """.format(label, basename, screenshot_name, int(NES_WIDTH * scale), int(NES_HEIGHT * scale), 
               label, int(obj_x * scale), int(obj_y * scale), int((obj_x + obj_size[0]) * scale), 
               int((obj_y + obj_size[1]) * scale))

    with open(xml_filename, "w") as fn:
        fn.write(annotation_string)


    print("Annotation string:  {}".format(annotation_string))



def generate_screenshot(screen, bg_surface, background_img, object_img, obj_x=None, obj_y=None,
                        outdir=".", label="None", scale=2.0):
    screen.blit(bg_surface, (0, 0))
    if background_img is not None:
        screen.blit(background_img, (0, 0))
    screen.blit(object_img, (obj_x, obj_y))
    pygame.display.flip()

    for event in pygame.event.get():
        pass  # we need to get pygame.event.get() in order to display

    path = "{}/{}".format(outdir, label)
    create_path_if_not_exist(path)

    time_now = datetime.datetime.now()
    screenshot_name = "{}/{}-{:04d}-{:02d}-{:02d}-{:02d}{:02d}{:02d}-{}.jpg".format(path, label,
                                                                              time_now.year,
                                                                              time_now.month,
                                                                              time_now.day,
                                                                              time_now.hour,
                                                                              time_now.minute,
                                                                              time_now.second,
                                                                                    random.randint(0,10000))


    print("Screenshot name = {}".format(screenshot_name))
    print("path = {}".format(path))

    (x_size, y_size) = screen.get_rect().size
    pygame.image.save(pygame.transform.scale(screen, (int(x_size * scale), int(y_size * scale))), "{}".format(screenshot_name))

    # add the xml label file
    generate_label_file(screenshot_name, label, object_img, obj_x, obj_y, scale)


@click.command()
@click.argument('object')
@click.option('--background-img', help="Background image to use")
@click.option('--background-cols', help="Comma separated list of r,g,b (Example: 0,0,128). "
              "If None, a random colour is generated", default="None")
@click.option('--object-loc', help="x,y coordinates of where to place object (Example: 50,80)")
@click.option('--many', help="How many images to generate", default=1)
@click.option('--outdir', help="Where to store the training data", default="training")
@click.option('--label', help="Label for the images", default="None")
@click.option('--sleeptime', help="delay between each image generation", default=None)
@click.option('--scale', help="amount to scale the images by", default=2.0)
def handle_cmdline(object, background_img, background_cols, object_loc, many, outdir,
                   label, sleeptime, scale):
    """ A little utility program that lets you generate training data for the ai-player
        object detection.

        The basic idea is that you pass a background image and 'object' image, and the
        program will then place the object on top of the background image in a random
        location, and save the generated image together with the training mask.
    """
    print("in handle_cmdline:   object = {},   background = {}".format(object, background_img))

    # initialise pygame first (sadly this is required...)
    pygame.init()
    screen = pygame.display.set_mode((NES_WIDTH, NES_HEIGHT))

    # load image if defined
    (bg_img, _) = get_image(background_img)

    # load the object image
    print("Loading image")
    (object_img, img_size) = get_image(object)

    for i in range(0, many):
        # background surface - sits in here because we sometimes have random
        # background colours
        bg_surface = get_bg_surface(background_cols)

        print("Generating image {}".format(i))
        # find out where to place the object
        (obj_x, obj_y) = get_xy(object_loc, img_size)

        generate_screenshot(screen, bg_surface, bg_img, object_img, obj_x, obj_y, outdir,
                            label, scale)

        if sleeptime is not None:
            time.sleep(float(sleeptime))


if __name__ == "__main__":
    handle_cmdline()
