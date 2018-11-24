# Standard
import logging
import sys
import time

# Third Party
import pygame as pg

# Project
from harren.key_handler import KeyHandler
from harren.utils.pg_utils import get_font
from harren.levels import LEVEL_MAP

LOG = logging.getLogger(__name__)


class GameState(KeyHandler):

    def __init__(self, *args, **kwargs):
        pg.init()
        xres = kwargs.get('xres', 800)
        yres = kwargs.get('yres', 608)
        fullscreen = kwargs.get('fullscreen', False)
        self.caption = 'Harren'
        self.state = {
            'volume': 0.4,
            'current_time': 0.0,
            'current_level': 'game_select',
            'previous_level': 'load_screen',
        }
        self.level_instance = None

        # Set allowed event types
        pg.event.set_allowed([pg.KEYDOWN, pg.KEYUP, pg.QUIT])

        # Window title
        pg.display.set_caption(self.caption)

        if fullscreen:
            self.surface = pg.display.set_mode((xres, yres), pg.FULLSCREEN)
        else:
            self.surface = pg.display.set_mode((xres, yres))

        self.clock = pg.time.Clock()
        self.fps = kwargs.get('fps', 60)
        LOG.debug('Launching with target FPS: %s', self.fps)

        # Draw the loading screen
        load_screen = LEVEL_MAP['load_screen'](self)
        load_screen()   # Initial draw
        pg.display.flip()
        time.sleep(2)   # Give some artificial time to display the load screen

    def _get_current_time(self):
        return self.state.get('current_time', 0.0)

    def _set_current_time(self, value):
        if isinstance(value, int):
            value = float(value)
        if not isinstance(value, float):
            raise TypeError('"current_time" attribute must be a float or int')
        self.state['current_time'] = value

    current_time = property(_get_current_time, _set_current_time)
    """Simple property to get and set time values."""

    def _get_current_level(self):
        return self.state.get('current_level', 0.0)

    def _set_current_level(self, value):
        self.state['current_level'] = value

    current_level = property(_get_current_level, _set_current_level)
    """Simple property to get and set the current level name."""

    def _get_previous_level(self):
        return self.state.get('previous_level', 0.0)

    def _set_previous_level(self, value):
        self.state['previous_level'] = value

    previous_level = property(_get_previous_level, _set_previous_level)
    """Simple property to get and set the previous level name."""

    @property
    def screen_rectangle(self):
        """Return the current display surface rectangle."""
        return self.surface.get_rect()

    @property
    def font(self):
        """Return the main font."""
        try:
            return self._main_font
        except AttributeError:
            self._main_font = get_font('Triforce.ttf', size=20)
        return self._main_font

    @property
    def large_font(self):
        """Return the main font large size."""
        try:
            return self._large_font
        except AttributeError:
            self._large_font = get_font('Triforce.ttf', size=40)
        return self._large_font

    def main(self):
        """Main loop for entire program."""
        while True:
            # The level has changed, load the new level
            if (self.current_level != self.previous_level or
                    self.level_instance is None):
                self.level_instance = LEVEL_MAP[self.current_level](self)
                self.previous_level = self.current_level

            pressed = pg.key.get_pressed()
            alt_held = pressed[pg.K_LALT] or pressed[pg.K_RALT]
            # ctrl_held = pressed[pg.K_LCTRL] or pressed[pg.K_RCTRL]

            events = pg.event.get()
            keydown = []
            # Prioritize quit events but populate the keydown events
            for event in events:
                # Handle quit event gracefully
                if event.type == pg.QUIT:
                    LOG.info('Exiting...')
                    self._exit()

                if event.type == pg.KEYDOWN:
                    # Pressing ALT-F4 also exits the game loop
                    if event.key == pg.K_F4 and alt_held:
                        LOG.info('Exiting...')
                        self._exit()
                    keydown.append(event)

            self.current_time = pg.time.get_ticks()
            self.level_instance.draw()
            pg.display.flip()
            self.clock.tick(self.fps)

        LOG.info('Exiting...')
        self._exit()

    @staticmethod
    def _exit(code=0):
        try:
            pg.display.quit()
        except Exception:
            pass
        try:
            pg.quit()
        except Exception:
            pass
        sys.exit(code)
