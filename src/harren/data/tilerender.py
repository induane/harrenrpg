"""This is a test of using the pytmx library with Tiled."""
import logging

import pygame as pg
from harren.pytmx.util_pygame import load_pygame
from harren.pytmx import TiledObjectGroup, TiledImageLayer, TiledTileLayer

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

        if self.tmx_data.background_color:
            print(dir(self.tmx_data))
            try:
                surface.fill(self.tmx_data.background_color)
            except Exception:
                print('Background Color: {}'.format(self.tmx_data.background_color))
                try:
                    surface.fill(self.tmx_data.backgroundcolor)
                except Exception:
                    LOG.exception('Ooops, cannot render bg')

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, TiledTileLayer):
                for x, y, gid in layer:
                    tile = gt(gid)
                    if tile:
                        surface.blit(tile, (x * tw, y * th))
            elif isinstance(layer, TiledObjectGroup):
                pass
            elif isinstance(layer, TiledImageLayer):
                image = gt(layer.gid)
                if image:
                    surface.blit(image, (0, 0))

    def make_2x_map(self):
        temp_surface = pg.Surface(self.size)
        self.render(temp_surface)
        temp_surface = pg.transform.scale2x(temp_surface)
        return temp_surface
