from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class LoadScreen(BaseLevel):
    name = 'loadscreen'

    def __init__(self, game_loop, **kwargs):
        kwargs['images'] = ['game_title.png']
        kwargs['exclude_players'] = True
        super(LoadScreen, self).__init__('load.tmx', game_loop, **kwargs)
