from __future__ import unicode_literals, absolute_import

# Standard
import logging

# Third Party
import pygame as pg

LOG = logging.getLogger(__name__)


class Player(pg.sprite.Sprite):

    def __init__(self, *args, **kwargs):
        self.game_loop = kwargs.pop('game_loop')
        super(Player, self).__init__(*args, **kwargs)

    @staticmethod
    def pygame_to_tile(rect):
        """Given a rectangle convert to tile coordinates."""
        def _calc_coord(v):
            if v == 0:
                coord = 0
            elif v % 32 == 0:
                coord = v / 32
            else:
                coord = 0
            return coord
        return (_calc_coord(rect.x), _calc_coord(rect.y))

    @staticmethod
    def center_player(rect_pos):
        """Adjust sprite position to be centered on tile."""
        diff = rect_pos % 32
        if diff <= 16:
            rect_pos - diff
        else:
            rect_pos + diff
