import math

import pygame

from core import fx as FX
from entities.EntityBase import EntityBase


class Checkpoint(EntityBase):
    def __init__(self, screen, x, y, level, sound):
        super().__init__(x, y - 1, 0)
        self.obeyGravity = False
        self.screen = screen
        self.sound = sound
        self.type = "Checkpoint"
        self.tile_pos = (x, y)
        self.activated = False
        self.pulse = 0

    def activate(self):
        if self.activated:
            return
        self.activated = True
        self.sound.play_sfx(self.sound.powerup_appear)
        FX.explosion(self.rect.centerx, self.rect.y, (80, 255, 140))

    def update(self, camera):
        self.pulse += 0.15
        x = self.rect.x + camera.x
        y = self.rect.y
        # poste
        pygame.draw.rect(self.screen, (90, 95, 110), (x + 14, y - 16, 4, 48))
        pygame.draw.rect(self.screen, (60, 65, 80), (x + 8, y + 28, 16, 4))
        # luz
        if self.activated:
            radius = 6 + int(2 * math.sin(self.pulse))
            color = (80, 255, 140)
        else:
            radius = 6
            color = (120, 120, 130)
        pygame.draw.circle(self.screen, color, (x + 16, y - 20), radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (x + 16, y - 20), 2)
