from __future__ import unicode_literals, absolute_import

# Standard
import logging
import sys
import time

# Third Party
import pygame as pg

# Project
from harren.utils.pg_utils import get_font
from harren.levels import LEVEL_MAP

LOG = logging.getLogger(__name__)


class GameState(object):

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
            'player1': {},
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
        self.level_has_changed = False
        LOG.debug('Launching with target FPS: %s', self.fps)

        # Draw the loading screen
        load_screen = LEVEL_MAP['load_screen'](self)
        load_screen()   # Initial draw
        pg.display.flip()
        time.sleep(0.5)   # Give some artificial time to display the load screen

    def set_state(self, state_dict):
        """Given a dict set the state values."""
        self.state.update(state_dict)

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
        if value not in LEVEL_MAP:
            raise ValueError('Unknown level: {}'.format(value))

        if value != self.state['current_level']:
            self.state['previous_level'] = self.state['current_level']
            self.state['current_level'] = value
            self.level_has_changed = True

    current_level = property(_get_current_level, _set_current_level)
    """Property to get and set the current level name."""

    def _get_previous_level(self):
        return self.state.get('previous_level', 0.0)

    def _set_previous_level(self, value):
        self.state['previous_level'] = value

    previous_level = property(_get_previous_level, _set_previous_level)
    """Simple property to get and set the previous level name."""

    @property
    def screen_rectangle(self):
        """Return the current display surface rectangle."""
        try:
            return self._screen_rect
        except AttributeError:
            self._screen_rect = self.surface.get_rect()
        return self._screen_rect

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

    @staticmethod
    def route_keys(keys, level_instance):
        if keys[pg.K_UP]:
            level_instance.up_pressed()
        if keys[pg.K_DOWN]:
            level_instance.down_pressed()
        if keys[pg.K_LEFT]:
            level_instance.left_pressed()
        if keys[pg.K_RIGHT]:
            level_instance.right_pressed()
        if keys[pg.K_SPACE]:
            level_instance.space_pressed()
        if keys[pg.K_ESCAPE]:
            level_instance.escape_pressed()
        if keys[pg.K_KP_ENTER]:
            level_instance.enter_pressed()
        if keys[pg.K_RETURN]:
            level_instance.enter_pressed()

    def main(self):
        """Main loop for entire program."""
        while True:
            LOG.debug('Frames Per Second: %s', self.clock.get_fps())
            # If the level has changed, load the new level
            if self.level_has_changed or self.level_instance is None:
                self.level_instance = LEVEL_MAP[self.current_level](self)
                self.level_has_changed = False

            events = pg.event.get()
            keys = pg.key.get_pressed()
            alt_held = keys[pg.K_LALT] or keys[pg.K_RALT]

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

                    # If the level requests only keydown events, route them
                    # here
                    if self.level_instance.keydown_only:
                        self.route_keys(keys, self.level_instance)

            # If we aren't only watching for keydown events, route keys once
            # per gameloop
            if not self.level_instance.keydown_only:
                self.route_keys(keys, self.level_instance)

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
