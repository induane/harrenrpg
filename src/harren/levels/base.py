from __future__ import unicode_literals, absolute_import

# Standard
import os
import logging
import random

# Third Party
import pygame as pg
from six import string_types

# Project
from harren import resources
from harren.key_handler import KeyHandler
from harren.tilerender import TileRenderer
from harren.utils.pg_utils import get_image, load_music

LOG = logging.getLogger(__name__)


class BaseLevel(KeyHandler):

    def __init__(self, filename, game_loop, **kwargs):
        self.map_filename = filename
        self.map_path = os.path.join(resources.TMX_FOLDER, filename)
        self.game_loop = game_loop
        self.images = kwargs.get('images', [])
        self.music = kwargs.get('music', None)

    def __call__(self):
        self.start()

    def start(self):
        LOG.debug('Map properties: %s', self.map_data)
        self.draw()
        self.play_music()

    @property
    def font(self):
        return self.game_loop.font

    @property
    def large_font(self):
        return self.game_loop.large_font

    @property
    def tmx_data(self):
        return self.tile_renderer.tmx_data

    @property
    def map_data(self):
        return self.tile_renderer.tmx_data.properties

    @property
    def music_file(self):
        """Randomly returns a music file if more than one are specified."""
        if not hasattr(self, '_music_files'):
            # Load all properties starting with "music"
            music_files = []
            for key, value in self.map_data.items():
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
    def tile_renderer(self):
        try:
            return self._tile_renderer
        except AttributeError:
            self._tile_renderer = TileRenderer(self.map_path)
        return self._tile_renderer

    @property
    def game_screen(self):
        return self.game_loop.surface

    @property
    def screen_rectangle(self):
        return self.game_loop.surface.get_rect()

    def play_music(self):
        if self.music_file:
            load_music(self.music_file)
            pg.mixer.music.set_volume(self.state['volume'])
            pg.mixer.music.play(-1)

    def draw(self):
        map_image = self.tile_renderer.make_2x_map()
        map_rect = map_image.get_rect()
        viewport = self.game_screen.get_rect()
        surface = pg.Surface((map_rect.width, map_rect.height)).convert()

        # Draw map first
        surface.blit(map_image, viewport, viewport)

        # If there are any images, draw them
        for image in self.images:
            # If there is no location data tuple, just blit to the middle
            if isinstance(image, string_types):
                img = get_image(image)
                img_rect = img.get_rect()
                img_rect.center = viewport.center
                surface.blit(img, img_rect)
            else:
                # Assuming a data tuple of path, x, y
                img_path, x, y = image
                img = get_image(img_path)
                img_rect = img.get_rect()
                img_rect.midbottom = self.viewport.midbottom
                img_rect.y = y
                img_rect.x = x
                surface.blit(img, img_rect)

        # Draw any text on the surface
        self.draw_text(surface)

        # Next maybe the player(s)
        # NOT IMPLEMENTED

        # Next maybe a menu
        # NOT IMPLEMENTED

        # Finally any dialog
        # NOT IMPLEMENTED

        # LOG.debug('blitting to actual screen surface')
        self.game_screen.blit(surface, (0, 0), viewport)

    def draw_text(self, surface):
        pass

    def get_colliders(self):
        """
        Colliders are invisible objects used for collision detection.

        To create a blocker in tiled, set the name or type to "blocker". It is
        preferable to use the 'type' field but for now the name field is also
        supported.
        """
        blockers = []
        for obj in self.tile_renderer.tmx_data.objects:
            properties = obj.__dict__
            name = properties.get('name')
            asset_type = properties.get('type')
            if asset_type == 'blocker' or name == 'blocker':
                left = properties['x'] * 2
                top = ((properties['y']) * 2) - 32
                blocker = pg.Rect(left, top, 32, 32)
                blockers.append(blocker)
        return blockers