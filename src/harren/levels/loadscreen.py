from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class LoadScreen(BaseLevel):

    def __init__(self, game_loop, **kwargs):
        kwargs['music'] = 'title_theme.ogg'
        super(LoadScreen, self).__init__(
            'load.tmx',
            game_loop,
            images=['game_title.png'],
            **kwargs
        )
