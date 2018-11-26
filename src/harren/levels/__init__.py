from __future__ import absolute_import

from harren.levels.base import BaseLevel
from harren.levels.loadscreen import LoadScreen
from harren.levels.game_select import GameSelect
from harren.levels.nohnaim import Nohnaim

LEVEL_MAP = {
    'game_select': GameSelect,
    'load_screen': LoadScreen,
    'nohnaim': Nohnaim,
}


__all__ = (
    'BaseLevel',
    'LEVEL_MAP',
    'LoadScreen',
    'Nohnaim',
)
