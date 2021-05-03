# Standard
import logging
from typing import Callable, Union

LOG = logging.getLogger(__name__)


def convert_to_bool(value: Union[str, int]) -> bool:
    """Convert a few common variations of "true" and "false" to bool."""
    if isinstance(value, int):
        return bool(int)

    value = value.strip()
    # Handle "1" and "0" string values
    try:
        return bool(int(value))
    except Exception:
        pass

    value = value.lower()
    if value in ('true', 'yes', '1', 'evet', 'y', ):
        return True
    if value in ('false', 'no', '0', 'hiyur', 'n', ):
        return False
    raise ValueError(f"Could not convert '{value}' to a boolean value")


class DefaultORM:
    backgroundcolor: Callable = str
    bold: Callable = convert_to_bool
    color: Callable = str
    columns: Callable = int
    compression: Callable = str
    draworder: Callable = str
    duration: Callable = int
    encoding: Callable = str
    firstgid: Callable = int
    fontfamily: Callable = str
    format: Callable = str
    gid: Callable = int
    halign: Callable = str
    height: Callable = float
    hexsidelength: Callable = float
    id: Callable = int
    italic: Callable = convert_to_bool
    kerning: Callable = convert_to_bool
    margin: Callable = int
    name: Callable = str
    nextobjectid: Callable = int
    offsetx: Callable = int
    offsety: Callable = int
    opacity: Callable = float
    orientation: Callable = str
    pixelsize: Callable = float
    points: Callable = str
    probability: Callable = float
    renderorder: Callable = str
    rotation: Callable = float
    source: Callable = str
    spacing: Callable = int
    staggeraxis: Callable = str
    staggerindex: Callable = str
    strikeout: Callable = convert_to_bool
    terrain: Callable = str
    tile: Callable = int
    tilecount: Callable = int
    tiledversion: Callable = str
    tileheight: Callable = int
    tileid: Callable = int
    tilewidth: Callable = int
    trans: Callable = str
    type: Callable = str
    underline: Callable = convert_to_bool
    valign: Callable = str
    value: Callable = str
    version: Callable = str
    visible: Callable = convert_to_bool
    width: Callable = float
    wrap: Callable = convert_to_bool
    x: Callable = float
    y: Callable = float

    def convert_value(self, key: str, value: str) -> Union[bool, float, int, str]:
        """Convert a value based on a mapping type."""
        func = getattr(self, key, str) or str
        return func(value)


class HWIntORM(DefaultORM):
    """Object mapper for TiledMaps."""
    height: Callable = int
    width: Callable = int


class TileFlags:

    __slots__ = (
        'flipped_horizontally',
        'flipped_vertically',
        'flipped_diagonally'
    )

    def __init__(self, a: bool, b: bool, c: bool):
        self.flipped_horizontally: bool = a
        self.flipped_vertically: bool = b
        self.flipped_diagonally: bool = c


class AnimationFrame:

    __slots__ = ('gid', 'duration')

    def __init__(self, gid, duration: int):
        self.gid = gid
        self.duration = duration

    def __getitem__(self, i):
        if i == 0:
            return self.gid
        elif i == 1:
            return self.duration
        elif i == -1:
            return self.duration
        elif i == -2:
            return self.gid
        raise IndexError('Out of range: %s', i)
