from __future__ import unicode_literals, absolute_import

# Standard
import logging
import os

# Third Party
import pygame as pg

# Project
from harren import resources

LOG = logging.getLogger(__name__)


def get_image(path, **kwargs):
    """
    Return a pygame image instance.

    If this is an image without alpha and you want to key the alpha channel
    from a specific color you can specify a colorkey tuple (r, g, b) and this
    will convert the graphic for you.
    """
    if not os.path.exists(path):
        new_path = os.path.join(resources.GFX_FOLDER, path)
        if os.path.exists(new_path):
            path = new_path
        else:
            raise OSError('Image "{}" not found'.format(path))
    colorkey = kwargs.get('colorkey', (255, 0, 255))
    img = pg.image.load(path)
    img.convert()
    if img.get_alpha():
        img = img.convert_alpha()
    else:
        img = img.convert()
        img.set_colorkey(colorkey)
    return img


def get_font(path, size=20):
    """Return a font instance from pygame for a given font."""
    if not path.lower().endswith('ttf'):
        path = '{}.ttf'.format(path)
    if not os.path.exists(path):
        new_path = os.path.join(resources.FONT_FOLDER, path)
        if os.path.exists(new_path):
            path = new_path
        else:
            raise OSError('Font "{}" not found'.format(path))
    path = os.path.join(resources.FONT_FOLDER, path)
    return pg.font.Font(path, size)


def load_music(path):
    """Load a song."""
    if not os.path.exists(path):
        new_path = os.path.join(resources.MUSIC_FOLDER, path)
        if os.path.exists(new_path):
            path = new_path
        else:
            raise OSError('Music "{}" not found'.format(path))
    return pg.mixer.music.load(path)
