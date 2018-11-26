from __future__ import unicode_literals, absolute_import

# Standard
import logging

# Third Party
import pygame as pg

# Project
from harren.utils import pg_utils

LOG = logging.getLogger(__name__)


class Player(pg.sprite.Sprite):

    def __init__(self, sprite_path, **kwargs):
        initial_direction = kwargs.get('direction', 'down_1')
        self.game_loop = kwargs.pop('game_loop')
        self.sprite_data = pg_utils.get_sprite_map(sprite_path)
        self.left_images = (
            self.sprite_data['left_1'],
            self.sprite_data['left_2'],
        )
        self.right_images = (
            self.sprite_data['right_1'],
            self.sprite_data['right_2'],
        )
        self.up_images = (
            self.sprite_data['up_1'],
            self.sprite_data['up_2'],
        )
        self.down_images = (
            self.sprite_data['down_1'],
            self.sprite_data['down_2'],
        )
        self.image = self.sprite_data[initial_direction]
        self.rect = self.image.get_rect()
        self.state = 'resting'
        self.y_velocity = 0
        self.x_velocity = 0
        super(Player, self).__init__(**kwargs)

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

    # def animate(self, freq=100):
    #     """Adjust sprite image frame based on timer."""
    #     if (self.current_time - self.timer) > freq:
    #         if self.index < (len(self.image_list) - 1):
    #             self.index += 1
    #         else:
    #             self.index = 0
    #         self.timer = self.current_time
    #     self.image = self.image_list[self.index]
