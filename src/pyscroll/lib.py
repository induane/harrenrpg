# Standard
from contextlib import contextmanager
from typing import Tuple


@contextmanager
def surface_clipping_context(surface, clip):
    original = surface.get_clip()
    surface.set_clip(clip)
    yield
    surface.set_clip(original)


def rect_to_bb(rect):
    x, y, w, h = rect
    return x, y, x + w - 1, y + h - 1


def hex_to_rgb(hex_str: str) -> Tuple[str, str, str]:
    """Convert html hex codes to RGB tuple."""
    hex_str = hex_str.strip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))
