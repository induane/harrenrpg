from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class Overworld(BaseLevel):
    name = 'overworld'

    def __init__(self, game_loop, **kwargs):
        super(Overworld, self).__init__(
            'harren_map.tmx',
            game_loop,
            **kwargs
        )
