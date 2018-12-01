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
        'current_time',
        'down_images',
        'game_loop',
        'image',
        'index',
        'initial_state',
        'left_images',
        'previous_state',
        'rect',
        'right_images',
        'state',
        'teleport_target',
        'up_images',
        'x_velocity',
        'y_velocity',
    )

    def __init__(self, game_loop, sprite_path, **kwargs):
        super(Player, self).__init__()
        self.game_loop = game_loop
        self.initial_state = 'resting'
        sprite_data = pg_utils.get_sprite_map(sprite_path)

        self.left_images = (sprite_data['left_1'], sprite_data['left_2'])
        self.right_images = (sprite_data['right_1'], sprite_data['right_2'])
        self.up_images = (sprite_data['up_1'], sprite_data['up_2'])
        self.down_images = (sprite_data['down_1'], sprite_data['down_2'])

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

    def _transform_image(self, image):
        """Scale down the image if scale down is set."""
        if not self.scale_down:
            return image
        orig_rect = image.get_rect()
        new_width = int(orig_rect.width / 2)
        new_height = int(orig_rect.height / 2)
        return pg.transform.scale(image, (new_width, new_height))

    def _get_img_set(self, state):
        """From a given state return a tuple of images."""
        if state == 'move-left':
            images = self.left_images
        elif state == 'move-right':
            images = self.right_images
        elif state == 'move-up':
            images = self.up_images
        elif state == 'move-down':
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
                    self.index = 1
                else:
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
