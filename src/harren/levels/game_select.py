from __future__ import absolute_import, unicode_literals

# Standard
import logging

# Project
from harren.levels.base import BaseLevel

LOG = logging.getLogger(__name__)


class GameSelect(BaseLevel):

    def __init__(self, game_loop, **kwargs):
        super(GameSelect, self).__init__(
            'load.tmx',
            game_loop,
            images=['title_box_empty.png'],
            **kwargs
        )

    def _draw_text(self, surface, **kwargs):
        """Custom text draw that can move the select arrow."""
        text = self.large_font.render('Select', True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.midtop = self.screen_rectangle.midtop
        text_rect.centerx = self.screen_rectangle.centerx
        text_rect.y += 60
        surface.blit(text, text_rect)

        new_game_text = self.font.render('New Game', True, (255, 255, 255))
        new_game_rect = new_game_text.get_rect()
        new_game_rect.midtop = self.screen_rectangle.midtop
        new_game_rect.centerx = self.screen_rectangle.centerx
        new_game_rect.y = text_rect.y + 60
        surface.blit(new_game_text, new_game_rect)

        slot1_text = self.font.render('Slot 1', True, (255, 255, 255))
        slot1_rect = slot1_text.get_rect()
        slot1_rect.midtop = self.screen_rectangle.midtop
        slot1_rect.centerx = self.screen_rectangle.centerx
        slot1_rect.y = new_game_rect.y + 40
        surface.blit(slot1_text, slot1_rect)

        # Always start on "new game" for now
        select = self.font.render('>> ', True, (255, 255, 255))
        select_rect = new_game_text.get_rect()
        select_rect.midleft = slot1_rect.midleft
        select_rect.x = select_rect.x - 50
        select_rect.y = new_game_rect.y
        surface.blit(select, select_rect)

    def draw_text(self, surface):
        self._draw_text(surface)
