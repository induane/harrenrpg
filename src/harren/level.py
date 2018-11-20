from __future__ import unicode_literals, absolute_import

# Standard
import os
import logging

from harren import resources
from harren.tilerender import TileRenderer

LOG = logging.getLogger(__name__)


class Level(object):

    def __init__(self, filename, **kwargs):
        map_path = os.path.join(resources.TMX_FOLDER, filename)
        self.tile_renderer = TileRenderer(map_path)
