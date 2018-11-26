from __future__ import absolute_import, unicode_literals

# Standard
import json
import logging
import os

# Project
from harren.levels.base import BaseLevel
from harren.resources import CONFIG_FOLDER

LOG = logging.getLogger(__name__)


class GameSelect(BaseLevel):
    name = 'game_select'

    def __init__(self, game_loop, **kwargs):
        super(GameSelect, self).__init__(
            'load.tmx',
            game_loop,
            images=['title_box_empty.png'],
            **kwargs
        )
        self.select_index = 0

    @property
    def save_files(self):
        """Return a list of all saved games."""
        try:
            return self._save_files
        except AttributeError:
            pass
        config_files = os.listdir(CONFIG_FOLDER)
        self._save_files = [x for x in config_files if x.endswith('.save')]
        return self._save_files

    def up_pressed(self, event):
        # Max index is the length of the array minux 1 but the select array
        # actually includes the new game option which is why we don't subtract
        # 1 here
        LOG.debug('UP pressed')
        max_idx = len(self.save_files)

        if self.select_index <= 0:
            self.select_index = max_idx
        else:
            self.select_index -= 1

    def down_pressed(self, event):
        # Max index is the length of the array minux 1 but the select array
        # actually includes the new game option which is why we don't subtract
        # 1 here
        LOG.debug('Down pressed')
        max_idx = len(self.save_files)

        if self.select_index >= max_idx:
            self.select_index = 0
        else:
            self.select_index += 1

    def space_pressed(self, event):
        if self.select_index == 0:
            self.game_loop.current_level = 'jova'
        else:
            path = os.path.join(
                CONFIG_FOLDER,
                self.save_files[self.select_index - 1]
            )
            LOG.debug('Opening save file %s', path)
            with open(path, 'rb') as f:
                state_dict = json.load(f)
            self.game_loop.set_state(state_dict)

    def _draw_text(self, surface, **kwargs):
        """Custom text draw that can move the select arrow."""
        text = self.large_font.render('Select', True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.midtop = self.screen_rectangle.midtop
        text_rect.centerx = self.screen_rectangle.centerx
        text_rect.y += 60
        surface.blit(text, text_rect)

        # Track rectange information for drawn info
        rectangle_data = {}

        new_game_text = self.font.render('New Game', True, (255, 255, 255))
        new_game_rect = new_game_text.get_rect()
        new_game_rect.midtop = self.screen_rectangle.midtop
        new_game_rect.centerx = self.screen_rectangle.centerx
        new_game_rect.y = text_rect.y + 60
        rectangle_data[0] = new_game_rect
        surface.blit(new_game_text, new_game_rect)

        for idx, fn in enumerate(self.save_files, start=1):
            display = fn.rstrip('.save')
            slot_text = self.font.render(display, True, (255, 255, 255))
            slot_rect = slot_text.get_rect()
            slot_rect.midtop = self.screen_rectangle.midtop
            slot_rect.centerx = self.screen_rectangle.centerx
            y_val = 40 * idx
            slot_rect.y = new_game_rect.y + y_val
            rectangle_data[idx] = slot_rect
            surface.blit(slot_text, slot_rect)

        # Given the current index value for the selections, draw an arrow.
        select = self.font.render('>> ', True, (255, 255, 255))
        select_rect = new_game_text.get_rect()
        select_rect.midleft = rectangle_data[self.select_index].midleft
        select_rect.x = select_rect.x - 50
        select_rect.y = rectangle_data[self.select_index].y
        surface.blit(select, select_rect)

    def draw_text(self, surface):
        self._draw_text(surface)
