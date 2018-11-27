from __future__ import unicode_literals, absolute_import

# Standard
import os
import logging
import random

# Third Party
from boltons.cacheutils import cachedproperty
from six import string_types
import pygame as pg

# Project
from harren import resources
from harren.player import Player
from harren.tilerender import render_tile
from harren.utils.pg_utils import get_image, load_music

LOG = logging.getLogger(__name__)


class BaseLevel(object):

    def __init__(self, filename, game_loop, **kwargs):
        self.map_filename = filename
        self.map_path = os.path.join(resources.TMX_FOLDER, filename)
        LOG.debug('Initializing level with map %s', self.map_path)
        self.game_loop = game_loop
        self.battles_allowed = kwargs.get('battles_allowed', False)
        self.exclude_players = kwargs.get('exclude_players', False)
        self.music = kwargs.get('music', None)
        self.keydown_only = False

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

    def _simple_draw(self):
        """Simple draw used in menus and other non-player based levels."""
        map_image = self.map_image
        map_rect = self.map_image.get_rect()
        viewport = self.game_screen.get_rect()
        surface = pg.Surface((map_rect.width, map_rect.height))

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

        self.game_screen.blit(surface, (0, 0), viewport)

    def draw(self):
        map_image = self.map_image
        map_rect = self.map_image.get_rect()
        viewport = self.game_screen.get_rect()
        surface = pg.Surface((map_rect.width, map_rect.height))
        colliders = self.custom_objects['colliders']
        portals = self.custom_objects['portals']

        # Center the viewport on player 1
        self.player1.update()
        viewport.center = self.player1.rect.center
        viewport.clamp_ip(map_rect)

        if self.player1.state.startswith('move'):
            orig_x = self.player1.rect.x
            orig_y = self.player1.rect.y
            check_box = self.player1.rect.move(
                self.player1.x_velocity,
                self.player1.y_velocity
            )
            for portal in portals:
                if portal['rect'].colliderect(check_box):
                    self.player1.state = 'teleporting'
                    self.player1.teleport_target = portal['teleport_target']
                    self.state['player1'] = self.player1.get_state()
                    self.game_loop.current_level = portal['destination']
                    return  # Abandon all processing and level jump

            for collider in colliders:
                if collider.colliderect(check_box):
                    self.player1.rect.x = orig_x
                    self.player1.rect.y = orig_y
                    self.player1.state = 'resting'
                    self.state['player1'] = self.player1.get_state()
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
                self.state['player1'] = self.player1.get_state()

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
        surface.blit(self.player1.image, self.player1.rect)

        self.game_screen.blit(surface, (0, 0), viewport)

    def draw_text(self, surface):
        pass

    @cachedproperty
    def player1(self):
        """
        Create a player instance.

        If starting fresh, load at the levels starting point. Otherwise,
        either restore a previous location or setup a teleport and look for a
        teleport target.
        """
        player1 = Player(self.game_loop, 'player.png')
        state_data = self.state['player1']
        if state_data:
            is_teleporting = state_data['state'] == 'teleporting'
            teleport_target = state_data.get('teleport_target')
            state_data['state'] = 'resting'
            state_data['x_velocity'] = 0
            state_data['y_velocity'] = 0
            state_data['teleport_target'] = None
            player1.set_state(state_data)

            # If the player was teleporting, place them at the starting point
            if is_teleporting:
                # Try to find a portal with target name if one available
                if teleport_target:
                    for p_target in self.custom_objects['portal_targets']:
                        if p_target.get('name') == teleport_target:
                            player1.rect.center = p_target['rect'].center
                            player1.rect.x = p_target['rect'].x
                            player1.rect.y = p_target['rect'].y
                            break
                    else:
                        LOG.warning('Could not find target portal %s',
                                    teleport_target)
                        # Fall back to start point
                        player1.rect.center = self.start_point.center
                        player1.rect.x = self.start_point.x
                        player1.rect.y = self.start_point.y
                # Otherwise use the start point
                else:
                    player1.rect.center = self.start_point.center
                    player1.rect.x = self.start_point.x
                    player1.rect.y = self.start_point.y
        else:
            player1.rect.center = self.start_point.center
            player1.rect.x = self.start_point.x
            player1.rect.y = self.start_point.y
        return player1

    @cachedproperty
    def custom_objects(self):
        """
        All important data types collected in a single iteration.

        Gathers colliders, portals, and start points.
        """
        colliders = []
        start_point = None
        portals = []
        portal_targets = []
        for obj in self.tmx_data.objects:
            properties = obj.__dict__
            name = properties.get('name')
            asset_type = properties.get('type')
            if asset_type == 'blocker' or name == 'blocker':
                left = properties['x'] * 2
                top = ((properties['y']) * 2)
                colliders.append(pg.Rect(left, top, 32, 32))
            elif not start_point and any((
                asset_type in ('start_point', 'start point', 'starting point'),
                name in ('start_point', 'start point', 'starting point'),
            )):
                left = properties['x'] * 2
                top = ((properties['y']) * 2) - 32
                start_point = pg.Rect(left, top, 32, 32)
            elif asset_type == 'portal_target':
                left = properties['x'] * 2
                top = ((properties['y']) * 2)
                portal_targets.append({
                    'name': name,
                    'rect': pg.Rect(left, top, 32, 32)
                })
            elif asset_type == 'portal' or name == 'portal':
                custom_properties = properties.get('properties', {})
                destination = custom_properties.get('destination')
                teleport_target = custom_properties.get('portal')
                if not destination:
                    LOG.warning('Portal at %s, %s missing destination.',
                                properties['x'], properties['y'])
                else:
                    left = properties['x'] * 2
                    top = ((properties['y']) * 2)
                    portals.append({
                        'name': name,
                        'rect': pg.Rect(left, top, 32, 32),
                        'destination': destination,
                        'teleport_target': teleport_target,
                    })
        return {
            'colliders': colliders,
            'start_point': start_point,
            'portals': portals,
            'portal_targets': portal_targets,
        }

    @cachedproperty
    def start_point(self):
        """
        Returns rectangle representing the starting point in the level.

        If more than one is found, the others will be ignored. If none are
        found a default one will be created at 0, 0
        """
        start_point = self.custom_objects['start_point']
        if not start_point:
            start_point = pg.Rect(0, 0, 32, 32)
        return start_point

    def down_pressed(self):
        if self.player1.state == 'resting':
            self.player1.state = 'move-down'
            self.player1.y_velocity = 4
            self.player1.x_velocity = 0

    def up_pressed(self):
        if self.player1.state == 'resting':
            self.player1.state = 'move-up'
            self.player1.y_velocity = -4
            self.player1.x_velocity = 0

    def left_pressed(self):
        if self.player1.state == 'resting':
            self.player1.state = 'move-left'
            self.player1.y_velocity = 0
            self.player1.x_velocity = -4

    def right_pressed(self):
        if self.player1.state == 'resting':
            self.player1.state = 'move-right'
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
