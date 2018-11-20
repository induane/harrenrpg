from __future__ import unicode_literals, absolute_import


def hex_to_rgb(hex_str):
    """Convert html hex codes to RGB tuple."""
    hex_str = hex_str.strip('#')
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2 ,4))
