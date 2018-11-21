from __future__ import unicode_literals, absolute_import

# Standard
import os
import logging

# Third Party
import pygame as pg

# Project
from harren import resources
from harren.key_handler import KeyHandler
from harren.tilerender import TileRenderer

LOG = logging.getLogger(__name__)


class Level(KeyHandler):

    def __init__(self, filename, screen, game_state, **kwargs):
        map_path = os.path.join(resources.TMX_FOLDER, filename)
        self.screen = screen
        self.tile_renderer = TileRenderer(map_path)
        self.game_state = game_state

    def draw(self):
        map_image = self.tile_renderer.make_2x_map()
        map_rect = map_image.get_rect()
        viewport = self.screen.get_rect(bottom=map_rect.bottom)
        surface = pg.Surface((map_rect.width, map_rect.height)).convert()

        # Draw map first
        surface.blit(map_image, viewport, viewport)

        # Next maybe the player(s)
        # NOT IMPLEMENTED

        # Finally any dialog
        # NOT IMPLEMENTED
