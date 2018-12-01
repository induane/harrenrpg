from __future__ import absolute_import, unicode_literals

# Standard
import logging
import os

# Third Party
from boltons.cacheutils import cachedproperty
from pytmx.util_pygame import load_pygame

# Project
from harren import resources
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class Overworld(BaseLevel):
    name = 'overworld'

    def __init__(self, game_loop, **kwargs):
        super(Overworld, self).__init__('harren_map.tmx', game_loop, **kwargs)

    @cachedproperty
    def tmx_data(self):
        try:
            return self.game_loop._overworld_cache
        except AttributeError:
            self.game_loop._overworld_cache = load_pygame(self.map_path)
        return self.game_loop._overworld_cache
