import sys
import logging

# Third Party
import pygame as pg

LOG = logging.getLogger(__name__)


class GameState(object):

    def __init__(self, *args, **kwargs):
        pg.init()
        xres = kwargs.get('xres', 800)
        yres = kwargs.get('yres', 608)
        fullscreen = kwargs.get('fullscreen', False)
        self.caption = 'Harren'

        # Set allowed event types
        pg.event.set_allowed([pg.KEYDOWN, pg.KEYUP, pg.QUIT])

        # Window title
        pg.display.set_caption(self.caption)

        if fullscreen:
            pg.display.set_mode((xres, yres), pg.FULLSCREEN)
        else:
            pg.display.set_mode((xres, yres))

        self.clock = pg.time.Clock()
        self.fps = kwargs.get('fps', 60)
        LOG.debug('Launching with target FPS: %s', self.fps)
        self.current_time = long(0.0)  # Initial time game counter

    @property
    def screen(self):
        return pg.display.get_surface()

    @property
    def screen_rectangle(self):
        """Return the size of the current display surface."""
        return self.screen.get_rect()

    def main(self):
        """Main loop for entire program."""
        while True:
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
            pg.display.update()
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
