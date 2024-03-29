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
    resource_path = os.path.join(resources.GFX_FOLDER, path)
    if not os.path.exists(resource_path):
        # Maybe we got an absolute path, check that
        if os.path.exists(path):
            resource_path = path
        else:
            raise OSError(f"Image '{path}' not found")

    LOG.debug("Getting image %s", resource_path)
    colorkey = kwargs.get("colorkey", (255, 0, 255))
    img = pg.image.load(resource_path)
    if img.get_alpha():
        img = img.convert_alpha()
    else:
        img = img.convert()
        img.set_colorkey(colorkey)
    return img


def get_sprite_image(x, y, width, height, sprite_sheet):
    """Extracts image from sprite sheet"""
    img = pg.Surface((width, height))
    img.blit(sprite_sheet, (0, 0), (x, y, width, height))
    img.set_colorkey((0, 0, 0))
    return img


def get_sprite_map(path, grid_size=16):
    """Make a dictionary of images from sprite sheet."""
    LOG.debug("Getting sprite map %s", path)
    sprite = get_image(path)
    col1 = grid_size * 2
    col2 = grid_size * 3
    return {
        "up_1": get_sprite_image(0, 0, grid_size, grid_size, sprite),
        "up_2": get_sprite_image(grid_size, 0, grid_size, grid_size, sprite),
        "down_1": get_sprite_image(col1, 0, grid_size, grid_size, sprite),
        "down_2": get_sprite_image(col2, 0, grid_size, grid_size, sprite),
        "left_1": get_sprite_image(0, grid_size, grid_size, grid_size, sprite),
        "left_2": get_sprite_image(grid_size, grid_size, grid_size, grid_size, sprite),  # noqa
        "right_1": get_sprite_image(col1, grid_size, grid_size, grid_size, sprite),  # noqa
        "right_2": get_sprite_image(col2, grid_size, grid_size, grid_size, sprite),  # noqa
    }


def get_font(path, size=20):
    """Return a font instance from pygame for a given font."""
    if not path.lower().endswith("ttf"):
        path = f"{path}.ttf"
    if not os.path.exists(path):
        new_path = os.path.join(resources.FONT_FOLDER, path)
        if os.path.exists(new_path):
            path = new_path
        else:
            raise OSError(f"Font '{path}' not found")
    path = os.path.join(resources.FONT_FOLDER, path)
    LOG.debug("Font %s size %s", path, size)
    return pg.font.Font(path, size)


def load_music(path):
    """Load a song."""
    if not os.path.exists(path):
        new_path = os.path.join(resources.MUSIC_FOLDER, path)
        if os.path.exists(new_path):
            path = new_path
        else:
            raise OSError(f"Music '{path}' not found")
    return pg.mixer.music.load(path)
