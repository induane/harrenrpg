from __future__ import unicode_literals, absolute_import

# Standard
import os
import logging
import random

# Third Party
from boltons.cacheutils import cachedproperty
from six import string_types
import pygame as pg
from pytmx.util_pygame import load_pygame
import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup

# Project
from harren import resources
from harren.player import Player
from harren.npc import StaticNPC
from harren.utils.dialog import dialog_from_props
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
        self.keydown_orig = self.keydown_only   # Stash for flipping back to
        self.current_dialog = []
        self.velocity = 2  # Default movement velocity

        LOG.debug('Populating image cache...')
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

        LOG.debug('Collecting TMX data...')
        # Collect tmx_data and a surface
        self.tmx_data = load_pygame(self.map_path)
        self.map_data = pyscroll.data.TiledMapData(self.tmx_data)
        self.map_layer = pyscroll.BufferedRenderer(
            self.map_data,
            self.game_screen.get_size(),
            clamp_camera=False,
            background_color=self.map_data.background_color,
            alpha=False,
        )
        self.map_layer.zoom = 2

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.scroll_group = PyscrollGroup(
            map_layer=self.map_layer,
            default_layer=3
        )
        if self.player1:
            self.scroll_group.add(self.player1)
        objects = self.custom_objects
        for s_npc in objects['static_npcs']:
            if s_npc.image:
                try:
                    self.scroll_group.add(s_npc)
                except Exception:
                    LOG.exception('Cannot add static npc')

    def __call__(self):
        self.start()

    def start(self):
        self.play_music()
        self.draw()

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
        pg.mixer.music.fadeout(100)
        if self.music_file:
            load_music(self.music_file)
            pg.mixer.music.set_volume(self.state['volume'])
            pg.mixer.music.play(-1)
        else:
            pg.mixer.music.fadeout(100)

    def _simple_draw(self):
        """Simple draw used in menus and other non-player based levels."""
        viewport = self.game_screen.get_rect()
        surface = pg.Surface((viewport.width, viewport.height))

        # draw the map and all sprites
        self.scroll_group.draw(surface)

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
        player1 = self.player1
        viewport = self.game_screen.get_rect()
        surface = pg.Surface((viewport.width, viewport.height))
        colliders = self.custom_objects['colliders']
        portals = self.custom_objects['portals']
        static_npcs = self.custom_objects['static_npcs']

        # Center the viewport on player 1
        player1.update()
        self.scroll_group.center(player1.rect)

        if player1.state.startswith('move'):
            orig_x = player1.rect.x
            orig_y = player1.rect.y
            check_box = player1.rect.move(
                player1.x_velocity,
                player1.y_velocity,
            )
            move_player = True

            for portal in portals:
                if portal['rect'].colliderect(check_box):
                    player1.state = 'teleporting'
                    player1.teleport_target = portal['teleport_target']
                    self.state['player1'] = player1.get_state()
                    self.game_loop.current_level = portal['destination']
                    return

            for s_npc in static_npcs:
                if s_npc.rect.colliderect(check_box):
                    self.reset_player1(orig_x, orig_y)
                    self.current_dialog = s_npc.dialog[:]  # Copy the dialog
                    move_player = False
                    break

            if move_player:
                for collider in colliders:
                    if collider.colliderect(check_box):
                        self.reset_player1(orig_x, orig_y)
                        break

            if move_player is True:
                player1.rect.move_ip(player1.x_velocity, player1.y_velocity)

            if (player1.rect.x % 16 == 0 and player1.rect.y % 16 == 0):
                player1.state = 'resting'
                self.state['player1'] = player1.get_state()

        # Collect all images to blit
        images_to_blit = []

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
            images_to_blit.append((img, img_rect))

        # Draw the main scroll group
        self.scroll_group.draw(surface)

        # Draw all collected images to blit
        surface.blits(images_to_blit, doreturn=False)

        # Draw any text on the surface
        self.draw_text(surface)

        # Draw any dialog
        self.draw_dialog(surface, viewport)

        self.game_screen.blit(surface, (0, 0), viewport)

    def draw_text(self, surface):
        pass

    def draw_dialog(self, surface, viewport):
        """Draw any current dialog."""
        if not self.current_dialog:
            return
        try:
            text = self.current_dialog[0]
        except Exception:
            LOG.exception('Could not draw dialog text.')
            return

        img = self.dialog_image
        img_rect = img.get_rect()
        img_rect.bottomright = viewport.bottomright
        img_rect.x -= 3
        img_rect.y -= 3
        surface.blit(img, img_rect)

        dialog_text = self.font_20.render(text, True, (255, 255, 255))
        dialog_text_rect = dialog_text.get_rect()
        dialog_text_rect.center = img_rect.center
        surface.blit(dialog_text, dialog_text_rect)

    def reset_player1(self, x, y):
        self.player1.rect.x = x
        self.player1.rect.y = y
        self.player1.x_velocity = 0
        self.player1.y_velocity = 0
        self.player1.state = 'resting'
        self.state['player1'] = self.player1.get_state()

    @cachedproperty
    def player1(self):
        """
        Create a player instance.

        If starting fresh, load at the levels starting point. Otherwise,
        either restore a previous location or setup a teleport and look for a
        teleport target.
        """
        player1 = Player(self.game_loop, 'player.png')
        player1.rect.center = self.start_point.center
        player1.rect.x = self.start_point.x
        player1.rect.y = self.start_point.y

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
        return player1

    @cachedproperty
    def dialog_image(self):
        return get_image('dialog_box.png')

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
        static_npcs = []
        pg_rect = pg.Rect
        for obj in self.tmx_data.objects:
            properties = obj.__dict__
            name = properties.get('name')
            asset_type = properties.get('type')
            if asset_type == 'blocker' or name == 'blocker':
                colliders.append(pg_rect(
                    properties['x'],
                    properties['y'], 16, 16
                ))
            elif not start_point and any((
                asset_type in ('start_point', 'start point', 'starting point'),
                name in ('start_point', 'start point', 'starting point'),
            )):
                start_point = pg_rect(
                    properties['x'],
                    properties['y'], 16, 16
                )
            elif asset_type == 'portal_target':
                portal_targets.append({
                    'name': name,
                    'rect': pg_rect(
                        properties['x'],
                        properties['y'], 16, 16
                    )
                })
            elif asset_type == 'portal' or name == 'portal':
                custom_properties = properties.get('properties', {})
                destination = custom_properties.get('destination')
                teleport_target = custom_properties.get('portal')
                if not destination:
                    LOG.warning('Portal at %s, %s missing destination.',
                                properties['x'], properties['y'])
                else:
                    portals.append({
                        'name': name,
                        'rect': pg_rect(
                            properties['x'],
                            properties['y'], 16, 16
                        ),
                        'destination': destination,
                        'teleport_target': teleport_target,
                    })
            elif asset_type == 'static_npc':
                custom_properties = properties.get('properties', {})
                sprite = custom_properties.get('sprite')
                static_npcs.append(StaticNPC(
                    self.game_loop,
                    sprite,
                    pg_rect(properties['x'], properties['y'], 16, 16),
                    dialog=dialog_from_props(custom_properties)
                ))

        return {
            'colliders': colliders,
            'start_point': start_point,
            'portals': portals,
            'portal_targets': portal_targets,
            'static_npcs': static_npcs,
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
            start_point = pg.Rect(0, 0, 16, 16)
        LOG.debug('Got start point %s', start_point)
        return start_point

    def _pop_dialog(self):
        try:
            d = self.current_dialog.pop(0)
        except IndexError:
            pass
        else:
            LOG.debug('%s dropped from dialog queue', d)

    def down_pressed(self):
        if self.current_dialog:
            return  # Don't do anything while in dialog mode
        if self.player1.state == 'resting':
            self.player1.state = 'move-down'
            self.player1.y_velocity = self.velocity
            self.player1.x_velocity = 0

    def up_pressed(self):
        if self.current_dialog:
            return  # Don't do anything while in dialog mode
        if self.player1.state == 'resting':
            self.player1.state = 'move-up'
            self.player1.y_velocity = self.velocity * -1
            self.player1.x_velocity = 0

    def left_pressed(self):
        if self.current_dialog:
            return  # Don't do anything while in dialog mode
        if self.player1.state == 'resting':
            self.player1.state = 'move-left'
            self.player1.y_velocity = 0
            self.player1.x_velocity = self.velocity * -1

    def right_pressed(self):
        if self.current_dialog:
            return
        if self.player1.state == 'resting':
            self.player1.state = 'move-right'
            self.player1.y_velocity = 0
            self.player1.x_velocity = self.velocity

    def space_pressed(self):
        accept_spaces = getattr(self, 'accept_spaces', True)
        if accept_spaces:
            self.player1.state = 'resting'
            self.player1.y_velocity = 0
            self.player1.x_velocity = 0
            self._pop_dialog()
            self.accept_spaces = False
        else:
            self.accept_spaces = True
        pg.time.delay(20)
        pg.event.clear()

    def escape_pressed(self):
        self.current_dialog = []
        self.accept_spaces = True
        pass

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
