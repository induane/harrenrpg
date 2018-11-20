"""Sprites for attacks."""
import pygame as pg

from harren.data import setup, tools
from harren.py_compat import range


class Fire(pg.sprite.Sprite):
    """Fire animation for attacks."""

    def __init__(self, x, y):
        super(Fire, self).__init__()
        self.spritesheet = setup.GFX['explosion']
        self.get_image = tools.get_image
        self.image_list = self.make_image_list()
        self.index = 0
        self.image = self.image_list[self.index]
        self.rect = self.image.get_rect(left=x, top=y)
        self.timer = 0.0

    def make_image_list(self):
        """
        Make a list of images to cycle through for the
        animation.
        """
        image_list = []

        for row in range(8):
            for column in range(8):
                posx = column * 128
                posy = row * 128
                new_image = self.get_image(posx, posy, 128, 128,
                                           self.spritesheet)
                image_list.append(new_image)

        return image_list

    def update(self):
        """
        Update fire explosion.
        """
        if self.index < (len(self.image_list) - 1):
            self.index += 1
            self.image = self.image_list[self.index]
        elif self.index == (len(self.image_list) - 1):
            self.kill()
