# Standard
import logging

# Third Party
import six
import pygame as pg

# Project
from harren.utils import color
from harren.pytmx.util_pygame import load_pygame
from harren.pytmx import TiledImageLayer, TiledTileLayer

LOG = logging.getLogger(__name__)


class Renderer(object):
    """This object renders tile maps from Tiled."""

    def __init__(self, filename):
        tm = load_pygame(filename, pixelalpha=True)
        self.size = tm.width * tm.tilewidth, tm.height * tm.tileheight
        self.tmx_data = tm

    def render(self, surface):
        tw = self.tmx_data.tilewidth
        th = self.tmx_data.tileheight
        gt = self.tmx_data.get_tile_image_by_gid

        bg_color = self.tmx_data.background_color
        if isinstance(bg_color, six.string_types):
            bg_color = color.hex_to_rgb(bg_color)
        if bg_color:
            surface.fill(bg_color)

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, TiledTileLayer):
                for x, y, gid in layer:
                    tile = gt(gid)
                    if tile:
                        surface.blit(tile, (x * tw, y * th))
            elif isinstance(layer, TiledImageLayer):
                image = gt(layer.gid)
                if image:
                    surface.blit(image, (0, 0))

    def make_2x_map(self):
        temp_surface = pg.Surface(self.size)
        self.render(temp_surface)
        temp_surface = pg.transform.scale2x(temp_surface)
        return temp_surface
