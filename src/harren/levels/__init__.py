from __future__ import absolute_import

# Standard
import os
from functools import partial

# Third Party
import pytoml as toml

from harren.levels.base import BaseLevel
from harren.levels.game_select import GameSelect
from harren.levels.loadscreen import LoadScreen
from harren.levels.overworld import Overworld
from harren.resources import DATA_FOLDER


LEVEL_MAP = {
    'game_select': GameSelect,
    'load_screen': LoadScreen,
    'overworld': Overworld,
}


def map_constructor(game_loop, **kwargs):
    name = kwargs.pop('name')
    filename = kwargs.pop('filename')
    return BaseLevel(filename, game_loop, name=name)


with open(os.path.join(DATA_FOLDER, 'maps.toml'), 'rb') as f:
    data = toml.load(f)
    print(data)

for values in data['maps'].values():
    LEVEL_MAP[values['name']] = partial(map_constructor, **values)


__all__ = (
    'BaseLevel',
    'LEVEL_MAP',
)
