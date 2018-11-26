# Standard
import logging

# Third Party
import pygame as pg
import six
from boltons.cacheutils import cachedproperty
from pytmx import TiledImageLayer, TiledTileLayer
from pytmx.util_pygame import load_pygame

# Project
from harren.utils import color


LOG = logging.getLogger(__name__)


class TileRenderer(object):
    """
    This object renders tile maps from Tiled.

    Map paths are expected to be absolute paths to a tmx file produced by the
    tile editor application "Tiled". The data is lazily evaluated so if the
    renderer is never utilized the data won't be loaded. This means it's safe
    to load a bunch of TileRenderer instances without paying a loading penalty.
    """

    def __init__(self, map_path):
        self.map_path = map_path

    @cachedproperty
    def tmx_data(self):
        return load_pygame(self.map_path, pixelalpha=True)

    @cachedproperty
    def size(self):
        tm = self.tmx_data
        return (tm.width * tm.tilewidth, tm.height * tm.tileheight)

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
            LOG.debug('Rendering layer: %s', layer.name)
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
        return pg.transform.scale2x(temp_surface)
