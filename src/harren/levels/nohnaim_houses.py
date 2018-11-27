from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class NohnaimHouse1(BaseLevel):
    name = 'nohnaim_house_1'

    def __init__(self, game_loop, **kwargs):
        super(NohnaimHouse1, self).__init__(
            'nohnaim_house_1.tmx',
            game_loop,
            **kwargs
        )


class NohnaimHouse2(BaseLevel):
    name = 'nohnaim_house_2'

    def __init__(self, game_loop, **kwargs):
        super(NohnaimHouse2, self).__init__(
            'nohnaim_house_2.tmx',
            game_loop,
            **kwargs
        )
