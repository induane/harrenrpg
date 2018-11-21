"""
This module initializes the display and
creates dictionaries of resources.
"""

import os
import pygame as pg
from harren.data import tools

GAME = 'START GAME'
ORIGINAL_CAPTION = 'The Legend of Harren'
DATA_FOLDER = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(DATA_FOLDER)
RESOURCES = os.path.join(PROJECT_ROOT, 'resources')

def init():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pg.init()
    pg.event.set_allowed([pg.KEYDOWN, pg.KEYUP, pg.QUIT])
    pg.display.set_caption(ORIGINAL_CAPTION)
    SCREEN = pg.display.set_mode((800, 608))
    SCREEN_RECT = SCREEN.get_rect()
    return SCREEN, SCREEN_RECT

FONTS = tools.load_all_fonts(os.path.join(RESOURCES, 'fonts'))
MUSIC = tools.load_all_music(os.path.join(RESOURCES, 'music'))
GFX = tools.load_all_gfx(os.path.join(RESOURCES, 'graphics'))
SFX = tools.load_all_sfx(os.path.join(RESOURCES, 'sound'))
TMX = tools.load_all_tmx(os.path.join(RESOURCES, 'tmx'))

FONT = pg.font.Font(FONTS['Triforce'], 20)
