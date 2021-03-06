from __future__ import unicode_literals, absolute_import

# Standard
import json
import logging
import os
import sys
import time

# Third Party
import pygame as pg
import pytoml as toml
from boltons.cacheutils import cachedproperty
from pytmx.util_pygame import load_pygame

# Project
from harren.levels import LEVEL_MAP
from harren.resources import CONFIG_FOLDER, DATA_FOLDER, TMX_FOLDER
from harren.utils.pg_utils import get_font

LOG = logging.getLogger(__name__)
LAST_SAVE_PATH = os.path.join(CONFIG_FOLDER, 'Last.save')


class GameState(object):

    def __init__(self, *args, **kwargs):
        pg.init()
        self.initialize_audio()

        self.xres = kwargs.get('xres', 800)
        self.yres = kwargs.get('yres', 600)
        fullscreen = kwargs.get('fullscreen', False)
        no_splash = kwargs.get('no_splash', False)
        self.sound_enabled = kwargs.get('sound_enabled', True)
        self.show_fps = False
        caption = 'Harren Press'
        self.state = {
            'volume': 0.4,
            'current_time': 0.0,
            'current_level': 'game_select',
            'previous_level': 'load_screen',
            'player1': {},
            'inventory': {},
            'quest_inventory': {'magic_item_1': 1},
            'quests': [],
            'completed_quests': [],
        }
        self.level_instance = None
        self.current_time = 0.0

        # Set allowed event types
        pg.event.set_allowed([pg.KEYDOWN, pg.KEYUP, pg.QUIT])

        # Window title
        pg.display.set_caption(caption)

        if fullscreen:
            self.surface = pg.display.set_mode(
                (self.xres, self.yres),
                pg.FULLSCREEN | pg.DOUBLEBUF | pg.HWSURFACE
            )
        else:
            self.surface = pg.display.set_mode(
                (self.xres, self.yres),
                pg.DOUBLEBUF | pg.HWSURFACE
            )

        self.clock = pg.time.Clock()
        self.level_has_changed = False

        # If we're displaying the splash screen go ahead and pre-load the
        # overworld map as caching that one is the most important
        if not no_splash:
            # Draw the loading screen
            load_screen = LEVEL_MAP['load_screen'](self)
            load_screen()   # Initial draw
            pg.display.flip()
            self.overworld_map  # Forces the overworld map to get cached

    def initialize_audio(self):
        """Setup the audio system."""
        loop = 3
        while True:
            LOG.info('Initializing audio system...')
            try:
                pg.mixer.init()
            except Exception:
                if loop <= 0:
                    LOG.exception('Unable to initialize audio system')
                    break
                else:
                    try:
                        pg.mixer.quit()
                    except Exception:
                        pass
                    time.sleep(1)
            else:
                break
            loop -= 1

    @cachedproperty
    def overworld_map(self):
        """Return the overworld map (caching on first access)"""
        map_path = os.path.join(TMX_FOLDER, 'harren_map.tmx')
        return load_pygame(map_path)

    @cachedproperty
    def quest_data(self):
        path = os.path.join(DATA_FOLDER, 'quest.toml')
        with open(path, 'rb') as f:
            data = toml.loads(f.read())
        return data

    @cachedproperty
    def npc_data(self):
        path = os.path.join(DATA_FOLDER, 'npc.toml')
        with open(path, 'rb') as f:
            data = toml.loads(f.read())
        return data

    def set_state(self, state_dict):
        """Given a dict set the state values."""
        self.state.update(state_dict)
        self.current_level = state_dict['current_level']
        self.level_has_changed = True

    def _get_current_level(self):
        return self.state.get('current_level', 'game_select')

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
        return self.state.get('previous_level', None)

    def _set_previous_level(self, value):
        self.state['previous_level'] = value

    previous_level = property(_get_previous_level, _set_previous_level)
    """Simple property to get and set the previous level name."""

    def _get_notification(self):
        """Return a notification if it hasn't expired."""
        start_time = getattr(self, '_notification_start_time', None)
        notification = getattr(self, '_notification_text', None)
        if not notification:
            return None

        # This shouldn't happen but if we have notification text but no
        # start time, clear the notification text
        if not start_time:
            self._notification_text = None
            return None

        # Show the notification for 4 seconds
        if self.current_time - start_time > 4000:
            self._notification_text = None
            return None

        return notification

    def _set_notification(self, text):
        """Set notification text to display."""
        self._notification_start_time = self.current_time
        self._notification_text = '* {}'.format(text)

    notification = property(_get_notification, _set_notification)

    @property
    def quest_inventory(self):
        return self.state['quest_inventory']

    @property
    def inventory(self):
        return self.state['inventory']

    @property
    def quests(self):
        return self.state['quests']

    @property
    def completed_quests(self):
        return self.state['completed_quests']

    @cachedproperty
    def screen_rectangle(self):
        """Return the current display surface rectangle."""
        return self.surface.get_rect()

    @cachedproperty
    def font_15(self):
        """Return the main font as 15pt."""
        return get_font('Triforce.ttf', size=15)

    @cachedproperty
    def font_20(self):
        """Return the main font."""
        return get_font('Triforce.ttf', size=20)

    @cachedproperty
    def font_25(self):
        """Return the main font."""
        return get_font('Triforce.ttf', size=25)

    @cachedproperty
    def font_40(self):
        """Return the main font large size."""
        return get_font('Triforce.ttf', size=40)

    @cachedproperty
    def font_60(self):
        """Return the main font large size."""
        return get_font('Triforce.ttf', size=60)

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

        # Do some initial lookups outside the loop for performance as dot
        # access has a minor performance penalty
        event_get = pg.event.get
        get_pressed = pg.key.get_pressed
        get_ticks = pg.time.get_ticks
        flip = pg.display.flip
        tick = self.clock.tick
        route_keys = self.route_keys

        while True:
            if self.current_level in ('quit', 'exit'):
                LOG.info('Exiting...')
                self._exit()
            # LOG.debug('Frames Per Second: %s', self.clock.get_fps())
            # If the level has changed, load the new level
            if self.level_has_changed or self.level_instance is None:
                self.level_instance = LEVEL_MAP[self.current_level](self)
                try:
                    self.level_instance.play_music()
                except pg.error:
                    LOG.exception('Unable to play music')
                self.level_has_changed = False

            events = event_get()
            keys = get_pressed()
            alt_held = keys[pg.K_LALT] or keys[pg.K_RALT]

            # Prioritize quit events but populate the keydown events
            for event in events:
                # Handle quit event gracefully
                if event.type == pg.QUIT:
                    LOG.info('Exiting...')
                    self._exit()

                if event.type == pg.KEYDOWN:
                    # Pressing ALT-F4 also exits the game loop and save
                    if event.key == pg.K_F4 and alt_held:
                        LOG.info('Exiting...')
                        self._exit()
                    if event.key == pg.K_F5 and alt_held:
                        self._save()
                    if event.key == pg.K_ESCAPE:
                        self.current_level = 'game_select'
                    if event.key == pg.K_F1 and alt_held:
                        if self.show_fps:
                            self.show_fps = False
                        else:
                            self.show_fps = True

                    # If the level requests only keydown events, route them
                    # here
                    if self.level_instance.keydown_only:
                        route_keys(keys, self.level_instance)

            # If we aren't only watching for keydown events, route keys once
            # per gameloop
            if not self.level_instance.keydown_only:
                route_keys(keys, self.level_instance)

            self.current_time = get_ticks()
            self.level_instance.draw()

            flip()
            tick(60)  # 60 FPS Target

        LOG.info('Exiting...')
        self._exit()

    def _save(self):
        """Save the game to Save Slot"""
        path = os.path.join(CONFIG_FOLDER, 'saved_game.save')
        with open(path, 'wb') as f:
            f.truncate()
            f.write(json.dumps(self.state, indent=4).encode('utf-8'))

    def _exit(self, code=0):
        try:
            pg.display.quit()
        except Exception:
            pass
        try:
            pg.quit()
        except Exception:
            pass
        with open(LAST_SAVE_PATH, 'wb') as f:
            f.truncate()
            f.write(json.dumps(self.state, indent=4).encode('utf-8'))
        sys.exit(code)
