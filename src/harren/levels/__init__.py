from __future__ import absolute_import

from harren.levels.base import BaseLevel
from harren.levels.loadscreen import LoadScreen
from harren.levels.game_select import GameSelect


LEVEL_MAP = {
    'game_select': GameSelect,
    'load_screen': LoadScreen,
}


__all__ = (
    'BaseLevel',
    'LoadScreen',
)
