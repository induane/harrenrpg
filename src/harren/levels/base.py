from __future__ import unicode_literals, absolute_import

# Standard
import os
import logging
import random

# Third Party
import pygame as pg
from boltons.cacheutils import cachedproperty
from six import string_types


# Project
from harren import resources
from harren.tilerender import render_tile
from harren.utils.pg_utils import get_image, load_music
from harren.player import Player

LOG = logging.getLogger(__name__)


class BaseLevel(object):

    def __init__(self, filename, game_loop, **kwargs):
        self.map_filename = filename
        self.map_path = os.path.join(resources.TMX_FOLDER, filename)
        LOG.debug('Initializing level with map %s', self.map_path)
        self.game_loop = game_loop

        self.music = kwargs.get('music', None)
        self.exclude_players = kwargs.get('exclude_players', False)
        self.keydown_only = False
        self._first_draw = True
        self._previous_center = None
        self.image_cache = []
        for image in kwargs.get('images', []):
            # If there is no location data tuple, just blit to the middle
            if isinstance(image, string_types):
                img = get_image(image)
                self.image_cache.append((img, None, None))
            else:
                # Assuming a data tuple of path, x, y
                img_path, x, y = image
                img = get_image(img_path)
                self.image_cache.append((img, x, y))

        # Collect tmx_data and a surface
        self.tmx_data, self.map_image = render_tile(self.map_path)

    def __call__(self):
        self.start()

    def start(self):
        self.draw()
        self.play_music()

    @property
    def font_20(self):
        return self.game_loop.font_20

    @property
    def font_40(self):
        return self.game_loop.font_40

    @property
    def font_60(self):
        return self.game_loop.font_60

    @cachedproperty
    def music_file(self):
        """Randomly returns a music file if more than one are specified."""
        if not hasattr(self, '_music_files'):
            # Load all properties starting with "music"
            music_files = []
            for key, value in self.tmx_data.properties.items():
                if key.lower().startswith('music'):
                    music_files.append(value)
            self._music_files = music_files

        if not self._music_files:
            LOG.debug('Map %s has no music specified', self.map_filename)
            return None  # No music specified in file

        # If there is only one, just return it every time
        if len(self._music_files) == 1:
            return self._music_files[0]

        rand_idx = random.randint(1, len(self._music_files)) - 1
        return self._music_files[rand_idx]

    @property
    def state(self):
        """Return the state from the parent game loop for convenience."""
        return self.game_loop.state

    @property
    def game_screen(self):
        return self.game_loop.surface

    def play_music(self):
        if self.music_file:
            load_music(self.music_file)
            pg.mixer.music.set_volume(self.state['volume'])
            pg.mixer.music.play(-1)

    def draw(self):
        map_image = self.map_image
        map_rect = self.map_image.get_rect()
        viewport = self.game_screen.get_rect()
        surface = pg.Surface((map_rect.width, map_rect.height))
        if not self.exclude_players:
            # Center the viewport on player 1
            viewport.center = self.player1.rect.center
            viewport.clamp_ip(map_rect)

            if self.player1.state == 'moving':
                orig_x = self.player1.rect.x
                orig_y = self.player1.rect.y
                check_box = self.player1.rect.move(
                    self.player1.x_velocity,
                    self.player1.y_velocity
                )
                for collider in self.colliders:
                    if collider.colliderect(check_box):
                        self.player1.rect.x = orig_x
                        self.player1.rect.y = orig_y
                        self.player1.state = 'resting'
                        self.state['player1']['location'] = (
                            self.player1.rect.x,
                            self.player1.rect.y,
                            self.player1.rect.center,
                        )
                        break
                else:
                    self.player1.rect.move_ip(
                        self.player1.x_velocity,
                        self.player1.y_velocity
                    )

                if (
                    self.player1.rect.x % 32 == 0 and
                    self.player1.rect.y % 32 == 0
                ):
                    self.player1.state = 'resting'
                    self.state['player1']['location'] = (
                        self.player1.rect.x,
                        self.player1.rect.y,
                        self.player1.rect.center,
                    )

        # Draw map first
        surface.blit(map_image, viewport, viewport)

        # If there are any images, draw them
        for img, x, y in self.image_cache:
            img_rect = img.get_rect()

            # If there is no location data tuple, just blit to the middle
            if x is None or y is None:
                img_rect.center = viewport.center
                surface.blit(img, img_rect)
            else:
                img_rect.midbottom = self.viewport.midbottom
                img_rect.y = y
                img_rect.x = x
            surface.blit(img, img_rect)

        # Draw any text on the surface
        self.draw_text(surface)

        # Next draw any players
        if not self.exclude_players:
            surface.blit(self.player1.image, self.player1.rect)

        self.game_screen.blit(surface, (0, 0), viewport)

    def draw_text(self, surface):
        pass

    @cachedproperty
    def player1(self):
        player1 = Player('player.png', game_loop=self.game_loop)
        try:
            x, y, center = self.state['player1']['location']
        except Exception:
            player1.rect.center = self.start_point.center
            player1.rect.x = self.start_point.x
            player1.rect.y = self.start_point.y
        else:
            player1.rect.center = center
            player1.rect.x = x
            player1.rect.y = y
        return player1

    @cachedproperty
    def colliders(self):
        """
        Colliders are invisible objects used for collision detection.

        To create a collider in tiled, set the name or type to "blocker". It is
        preferable to use the 'type' field but for now the name field is also
        supported.
        """
        colliders = []
        for obj in self.tmx_data.objects:
            properties = obj.__dict__
            name = properties.get('name')
            asset_type = properties.get('type')
            if asset_type == 'blocker' or name == 'blocker':
                left = properties['x'] * 2
                top = ((properties['y']) * 2)
                # top = ((properties['y']) * 2) - 32
                collider = pg.Rect(left, top, 32, 32)
                colliders.append(collider)
        return colliders

    @cachedproperty
    def start_point(self):
        """
        Returns rectangle representing the starting point in the level.

        If more than one is found, the others will be ignored. If none are
        found a default one will be created at 0, 0
        """
        for obj in self.tmx_data.objects:
            properties = obj.__dict__
            name = properties.get('name')
            asset_type = properties.get('type')
            if any((
                asset_type in ('start_point', 'start point', 'starting point'),
                name in ('start_point', 'start point', 'starting point'),
            )):
                left = properties['x'] * 2
                top = ((properties['y']) * 2) - 32
                start_point = pg.Rect(left, top, 32, 32)
                break
        else:
            start_point = pg.Rect(0, 0, 32, 32)
        return start_point

    def down_pressed(self):
        LOG.debug('Down pressed')
        if self.player1.state == 'resting':
            self.player1.state = 'moving'
            self.player1.y_velocity = 4
            self.player1.x_velocity = 0

    def up_pressed(self):
        LOG.debug('Up pressed')
        if self.player1.state == 'resting':
            self.player1.state = 'moving'
            self.player1.y_velocity = -4
            self.player1.x_velocity = 0


    def left_pressed(self):
        LOG.debug('Up pressed')
        if self.player1.state == 'resting':
            self.player1.state = 'moving'
            self.player1.y_velocity = 0
            self.player1.x_velocity = -4

    def right_pressed(self):
        LOG.debug('Up pressed')
        if self.player1.state == 'resting':
            self.player1.state = 'moving'
            self.player1.y_velocity = 0
            self.player1.x_velocity = 4

    def up_released(self):
        pass

    def left_released(self):
        pass

    def right_released(self):
        pass

    def w_released(self):
        pass

    def a_released(self):
        pass

    def s_released(self):
        pass

    def d_released(self):
        pass

    def enter_released(self):
        pass

    def space_released(self):
        pass

    def escape_released(self):
        pass

    def w_pressed(self):
        pass

    def a_pressed(self):
        pass

    def s_pressed(self):
        pass

    def d_pressed(self):
        pass

    def enter_pressed(self):
        pass

    def space_pressed(self):
        pass

    def escape_pressed(self):
        pass
