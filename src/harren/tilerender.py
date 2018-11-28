# Standard
import logging

# Third Party
import pygame as pg
import six
from pytmx import TiledImageLayer, TiledTileLayer
from pytmx.util_pygame import load_pygame

# Project
from harren.utils import color


LOG = logging.getLogger(__name__)


def render_tile(map_path):
    """
    This object renders tile maps from Tiled.

    Map paths are expected to be absolute paths to a tmx file produced by the
    tile editor application "Tiled".
    """
    tmx_data = load_pygame(map_path, pixelalpha=True)
    size = (
        tmx_data.width * tmx_data.tilewidth,
        tmx_data.height * tmx_data.tileheight,
    )
    try:
        temp_surface = pg.Surface(size)
    except Exception:
        LOG.exception('Error creating surface of size %s for %s',
                      size, map_path)
        raise
    tw = tmx_data.tilewidth
    th = tmx_data.tileheight
    gt = tmx_data.get_tile_image_by_gid
    bg_color = tmx_data.background_color

    if isinstance(bg_color, six.string_types):
        bg_color = color.hex_to_rgb(bg_color)
    if bg_color:
        temp_surface.fill(bg_color)

    for layer in tmx_data.visible_layers:
        if isinstance(layer, TiledTileLayer):
            for x, y, gid in layer:
                tile = gt(gid)
                if tile:
                    temp_surface.blit(tile, (x * tw, y * th))
        elif isinstance(layer, TiledImageLayer):
            image = gt(layer.gid)
            if image:
                temp_surface.blit(image, (0, 0))

    try:
        scaled_surface = pg.transform.scale2x(temp_surface)
    except Exception:
        # Probably too big, try returning the main surface
        return tmx_data, temp_surface
    else:
        return tmx_data, scaled_surface
