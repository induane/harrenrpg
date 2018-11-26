from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class Nohnaim(BaseLevel):
    name = 'nohnaim'

    def __init__(self, game_loop, **kwargs):
        super(Nohnaim, self).__init__(
            'nohnaim.tmx',
            game_loop,
            **kwargs
        )
