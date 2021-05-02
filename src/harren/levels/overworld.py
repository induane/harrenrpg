from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Third Party
from boltons.cacheutils import cachedproperty

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class Overworld(BaseLevel):
    name = 'overworld'

    def __init__(self, game_loop, **kwargs):
        super().__init__('harren_map.tmx', game_loop, **kwargs)

    @cachedproperty
    def tmx_data(self):
        return self.game_loop.overworld_map
