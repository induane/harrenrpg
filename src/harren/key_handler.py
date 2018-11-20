from __future__ import unicode_literals

# Standard
import logging

# Third Party
import pygame as pg

LOG = logging.getLogger(__name__)


class KeyHandler(object):
    """
    Handle key presses.

    This class is meant to be used as a Mixin. It will fire events for common
    key events which are implemented as no-op's. Any level which wishes to get
    notified of specific key presses can mix-in this class and utilize it.

    For the most basic key data just pass in an event list of KEYDOWN event to
    the process events list.

    TODO: Add utility for smooth motion when holding down keys - useful for
    in-game movement on maps.
    """

    def up_pressed(self, event):
        pass

    def down_pressed(self, event):
        pass

    def left_pressed(self, event):
        pass

    def right_pressed(self, event):
        pass

    def w_pressed(self, event):
        pass

    def a_pressed(self, event):
        pass

    def s_pressed(self, event):
        pass

    def d_pressed(self, event):
        pass

    def enter_pressed(self, event):
        pass

    def space_pressed(self, event):
        pass

    def escape_pressed(self, event):
        pass

    def process_events(self, events):
        """
        Process key events.

        Events should be a list of KEYDOWN events only. This will route calls
        to key functions, at most once per tick of the clock. It also returns
        a list of all key presses in the order that they occurred (but without
        any duplicates in a row - so you won't get K_w, K_w).
        """
        pressed = []
        for event in events:
            if event.key in pressed:
                if pressed[-1] != event.key:
                    pressed.append(event.key)
                continue  # Don't process more than once per tick

            if event.key == pg.K_UP:
                self.up_pressed(event)
            elif event.key == pg.K_DOWN:
                self.down_pressed(event)
            elif event.key == pg.K_LEFT:
                self.left_pressed(event)
            elif event.key == pg.K_RIGHT:
                self.right_pressed(event)
            elif event.key == pg.K_w:
                self.w_pressed(event)
            elif event.key == pg.K_a:
                self.a_pressed(event)
            elif event.key == pg.K_s:
                self.s_pressed(event)
            elif event.key == pg.K_d:
                self.d_pressed(event)
            elif event.key == pg.K_SPACE:
                self.space_pressed(event)
            elif event.key == pg.K_ESCAPE:
                self.escape_pressed(event)
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.enter_pressed(event)
            else:
                LOG.debug('Not handling key %s', event.key)
            pressed.append(event.key)
        return pressed
