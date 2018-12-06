from __future__ import unicode_literals, absolute_import

# Standard
import logging
import random

# Third Party
import pygame as pg
import six

# Project
from harren.utils import pg_utils

LOG = logging.getLogger(__name__)


class StaticNPC(pg.sprite.Sprite):
    """An NPC that doesn't move."""

    __slots__ = ('dialog', 'game_loop', 'image', 'rect')

    def __init__(self, game_loop, sprite_path, rect, **kwargs):
        super(StaticNPC, self).__init__()
        self.game_loop = game_loop
        self.dialog = kwargs.get('dialog', []) or []

        direction = kwargs.get('direction', 'down')
        if sprite_path:
            sprite_data = pg_utils.get_sprite_map(sprite_path)

            # We randomly select a particular version of the directional state
            # so that things seem slightly more lively
            rand = random.randint(1, 2)

            if direction == 'down':
                image = sprite_data['down_{}'.format(rand)]
            elif direction == 'up':
                image = sprite_data['up_{}'.format(rand)]
            elif direction == 'left':
                image = sprite_data['left_{}'.format(rand)]
            elif direction == 'right':
                image = sprite_data['right_{}'.format(rand)]
            else:
                raise Exception('Could not initialize sprite.')
            self.image = image
            self.rect = image.get_rect()
            self.rect.center = rect.center
        else:
            self.image = None
            self.rect = rect


class NPC(pg.sprite.Sprite):
    """An NPC that may be involved in quest data and stuff."""

    __slots__ = ('data', 'game_loop', 'image',
                 'rect', 'npc_data', 'name', 'base_dialog', 'alt_dialog')

    def __init__(self, game_loop, sprite_path, rect, **kwargs):
        super(NPC, self).__init__()
        self.game_loop = game_loop
        self.data = kwargs.get('data', {}) or {}

        direction = kwargs.get('direction', 'down')
        if sprite_path:
            sprite_data = pg_utils.get_sprite_map(sprite_path)

            # We randomly select a particular version of the directional state
            # so that things seem slightly more lively
            rand = random.randint(1, 2)

            if direction == 'down':
                image = sprite_data['down_{}'.format(rand)]
            elif direction == 'up':
                image = sprite_data['up_{}'.format(rand)]
            elif direction == 'left':
                image = sprite_data['left_{}'.format(rand)]
            elif direction == 'right':
                image = sprite_data['right_{}'.format(rand)]
            else:
                raise Exception('Could not initialize sprite.')
            self.image = image
            self.rect = image.get_rect()
            self.rect.center = rect.center
        else:
            self.image = None
            self.rect = rect

        # After popping the name and base_dialog keys from the quest data
        # dictionary, what remains should be exclusively quest information
        self.npc_data = self.game_loop.npc_data.get(self.data['name'], {})
        self.name = self.npc_data.pop('name', 'Jane')
        base_dialog = self.npc_data.pop('base_dialog', []) or []
        if isinstance(base_dialog, six.string_types):
            base_dialog = [base_dialog, ]
        self.base_dialog = base_dialog
        self.alt_dialog = self.npc_data.pop('alt_dialog', []) or []

    def interact(self):
        """
        Manage interactions by checking the game loop data. Returns dialog.

        This may involve checking inventory, adding items to the players
        inventory, or telling the game that a quest has started.
        """
        npc_data = self.npc_data
        quest_data = self.game_loop.quest_data
        current_quests = set(self.game_loop.quests)
        completed_quests = set(self.game_loop.completed_quests)
        quest_inventory = set(self.game_loop.quest_inventory.keys())
        inventory = set(self.game_loop.inventory.keys())

        LOG.debug('Quest Inventory: %s', quest_inventory)
        LOG.debug('Current Quests: %s', current_quests)
        LOG.debug('Completed Quests: %s', completed_quests)

        # If there isn't any extra information, just return the base dialog
        if not npc_data:
            return self.base_dialog[:]

        # Find out if we have an active quest for the current npc
        intersect = current_quests.intersection(quest_data.keys())

        # If we have an intersection, pull the relevant quest and use it
        if intersect:
            current_quest = intersect.pop()
            active_data = npc_data.get(current_quest)
            if not active_data:
                return self.base_dialog[:]

            shadow_items = active_data.get('shadow_items', [])

            LOG.debug("Active data: %s", active_data)

            for key, value in active_data.items():
                LOG.debug('Checking %s in active quest %s', key, current_quest)
                if key in ('start_quest', 'inventory', 'shadow_items',
                           'quest_complete', 'dialog', 'alt_dialog'):
                    continue

                if key in quest_inventory or key in inventory:
                    LOG.debug('%s found in inventory!', key)
                    if value.get('quest_complete', False) is True:
                        LOG.debug('Quest complete!')
                        self.game_loop.quests.pop(
                            self.game_loop.quests.index(current_quest)
                        )
                        self.game_loop.completed_quests.append(current_quest)

                        dialog = value.get('dialog') or []
                        if not dialog:
                            LOG.warning('NPC %s missing some quest dialog',
                                        self.name)
                        if isinstance(dialog, six.string_types):
                            dialog = [dialog, ]
                        return dialog[:]

            # If we have shadow items and they're already in the inventory,
            # return the alt dialog
            if shadow_items and quest_inventory.issuperset(shadow_items):
                dialog = active_data.get('alt_dialog') or []
                if not dialog:
                    return self.base_dialog[:]
                else:
                    if isinstance(dialog, six.string_types):
                        dialog = [dialog, ]
                    return dialog[:]

            # If we get to here then we have quest items that aren't in the
            # players quest inventory yet. Add them and return the normal
            # dialog
            if shadow_items:
                for item in shadow_items:
                    self.game_loop.quest_inventory.setdefault(item, 1)

                dialog = active_data.get('dialog') or []
                if not dialog:
                    LOG.warning('Quest %s missing dialog for npc %s',
                                current_quest, self.name)
                if isinstance(dialog, six.string_types):
                    dialog = [dialog, ]

                if active_data.get('quest_complete', False) is True:
                    self.game_loop.completed_quests.append(current_quest)
                return dialog[:]

            dialog = active_data.get('alt_dialog') or []
            if isinstance(dialog, six.string_types):
                dialog = [dialog, ]
            return dialog[:]

        # first serve!
        LOG.debug('No current quest, checking for new quest...')

        for quest_name, quest in npc_data.items():

            # If the quest is complete, don't do it twice
            if quest_name in completed_quests:
                LOG.debug('Already did this quest, moving along...')
                continue

            # If we haven't completed required quests, move along
            if not set(quest.get('requires', [])).issubset(completed_quests):
                LOG.debug('Requirements for %s not met', quest_name)
                continue

            quest_info = quest_data.get(quest_name) or {}

            # If we can start a quest, lets do it!
            if quest.get('start_quest', False) is True:
                self.game_loop.quests.append(quest_name)
                LOG.debug('Starting quest: %s', quest_name)
                dialog = quest.get('dialog') or []
                if not dialog:
                    LOG.warning('No dialog quest, returning generic...')
                    return ['You got a quest!', ]
                if isinstance(dialog, six.string_types):
                    dialog = [dialog, ]
                self.game_loop.notification = 'New quest! {}'.format(
                    quest_info.get('name', quest_name) or quest_name
                )
                return dialog[:]

        return self.base_dialog[:]
