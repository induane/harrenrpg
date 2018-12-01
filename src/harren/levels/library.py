from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class Library(BaseLevel):
    name = 'library'

    def __init__(self, game_loop, **kwargs):
        super(Library, self).__init__(
            'library.tmx',
            game_loop,
            **kwargs
        )
