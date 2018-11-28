from __future__ import unicode_literals, absolute_import

# Standard
import logging
import random

# Third Party
import pygame as pg

# Project
from harren.utils import pg_utils

LOG = logging.getLogger(__name__)


class StaticNPC(pg.sprite.Sprite):
    """An NPC that doesn't move."""

    __slots__ = ('dialog', 'game_loop', 'image', 'rect')

    def __init__(self, game_loop, sprite_path, rect, **kwargs):
        self.game_loop = game_loop
        self.dialog = kwargs.pop('dialog', []) or []

        direction = kwargs.pop('direction', 'down')
        sprite_data = pg_utils.get_sprite_map(sprite_path)

        # We randomly select a particular version of the directional state so
        # that things seem slightly more lively
        rand = random.randint(1, 2)

        if direction == 'down':
            self.image = sprite_data['down_{}'.format(rand)]
        elif direction == 'up':
            self.image = sprite_data['up_{}'.format(rand)]
        elif direction == 'left':
            self.image = sprite_data['left_{}'.format(rand)]
        elif direction == 'right':
            self.image = sprite_data['right_{}'.format(rand)]
        else:
            raise Exception('Could not initialize sprite.')
        self.rect = self.image.get_rect()
        self.rect.center = rect.center
        super(StaticNPC, self).__init__(**kwargs)
