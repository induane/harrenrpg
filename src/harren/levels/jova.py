from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class Jova(BaseLevel):
    name = 'jova'

    def __init__(self, game_loop, **kwargs):
        super(Jova, self).__init__(
            'jova.tmx',
            game_loop,
            **kwargs
        )
        LOG.debug('Starting point: %s', self.start_point)
