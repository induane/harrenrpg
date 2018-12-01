from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class Auria(BaseLevel):
    name = 'auria'

    def __init__(self, game_loop, **kwargs):
        super(Auria, self).__init__(
            'auria.tmx',
            game_loop,
            **kwargs
        )
