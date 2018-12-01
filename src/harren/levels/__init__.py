from __future__ import absolute_import

from harren.levels.overworld import Overworld
from harren.levels.nohnaim import Nohnaim
from harren.levels.loadscreen import LoadScreen
from harren.levels.game_select import GameSelect
from harren.levels.base import BaseLevel
from harren.levels.auria import Auria
from harren.levels.library import Library
from harren.levels.nohnaim_houses import (
    NohnaimHouse1,
    NohnaimHouse2,
    NohnaimSecret1,
)

LEVEL_MAP = {
    'auria': Auria,
    'game_select': GameSelect,
    'library': Library,
    'load_screen': LoadScreen,
    'nohnaim_house_1': NohnaimHouse1,
    'nohnaim_house_2': NohnaimHouse2,
    'nohnaim_secret_1': NohnaimSecret1,
    'nohnaim': Nohnaim,
    'overworld': Overworld,
}


__all__ = (
    'Auria',
    'BaseLevel',
    'LEVEL_MAP',
    'Library',
    'LoadScreen',
    'Nohnaim',
    'NohnaimHouse1',
    'NohnaimHouse2',
    'NohnaimSecret1',
    'Overworld',
)
