from __future__ import unicode_literals, absolute_import

# Standard
import logging

# Third Party
import pygame as pg

# Project
from harren.utils import pg_utils

LOG = logging.getLogger(__name__)


class Player(pg.sprite.Sprite):

    __slots__ = (
        'game_loop',
        'sprite_path',
        'initial_state',
        'current_time',
        'image',
        'rect',
        'state',
        'previous_state',
        'x_velocity',
        'y_velocity',
        'index',
        'teleport_target',
    )

    def __init__(self, game_loop, sprite_path, **kwargs):
        self.game_loop = game_loop
        self.sprite_path = sprite_path
        self.initial_state = 'resting'
        self.sprite_data = pg_utils.get_sprite_map(sprite_path)
        self.setup_images()

        self.current_time = self.game_loop.current_time
        self.image = self.down_images[0]
        self.rect = self.image.get_rect()
        self.state = self.initial_state
        self.previous_state = self.initial_state
        self.y_velocity = 0
        self.x_velocity = 0
        self.index = 0
        self.teleport_target = None
        super(Player, self).__init__(**kwargs)

    def setup_images(self):
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

    def _get_img_set(self, state):
        """From a given state return a tuple of images."""
        if state == 'move-left':
            LOG.debug('got move left images')
            images = self.left_images
        elif state == 'move-right':
            LOG.debug('got move right images')
            images = self.right_images
        elif state == 'move-up':
            LOG.debug('got move up images')
            images = self.up_images
        elif state == 'move-down':
            LOG.debug('got move down images')
            images = self.down_images
        elif state == 'resting':
            images = [self.down_images[0], self.down_images[0]]
        else:
            images = [self.down_images[0], self.down_images[0]]
        return images

    def update(self, frequency=100):
        """Update the timer and move animations around."""
        if (self.game_loop.current_time - self.current_time) > frequency:
            if self.state != 'resting':
                images = self._get_img_set(self.state)
                self.image = images[self.index]
                if self.index == 0:
                    LOG.debug('flipping index to 1')
                    self.index = 1
                else:
                    LOG.debug('flipping index to 0')
                    self.index = 0
            self.current_time = self.game_loop.current_time

    def get_state(self):
        """Return state data for the player."""
        rect = self.rect
        return {
            'state': self.state,
            'y_velocity': self.y_velocity,
            'x_velocity': self.x_velocity,
            'x': rect.x,
            'y': rect.y,
            'center': rect.center,
            'index': self.index,
            'initial_state': self.initial_state,
            'teleport_target': self.teleport_target,
        }

    def set_state(self, data):
        for key, value in data.items():
            if key == 'x':
                self.rect.x = value
            elif key == 'y':
                self.rect.y = value
            elif key == 'center':
                self.rect.center = value
            else:
                setattr(self, key, value)
