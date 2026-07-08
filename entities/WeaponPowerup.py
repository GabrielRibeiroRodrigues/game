import pygame

from classes.Collider import Collider
from entities.EntityBase import EntityBase
from traits.leftrightwalk import LeftRightWalkTrait


class WeaponPowerup(EntityBase):
    def __init__(self, screen, x, y, level, sound):
        super().__init__(x, y, 1.25)
        self.screen = screen
        self.level = level
        self.sound = sound
        self.type = "Item"
        self.collision = Collider(self, level)
        self.leftrightTrait = LeftRightWalkTrait(self, level)

    def update(self, camera):
        if not self.alive:
            return
        self.applyGravity()
        self.leftrightTrait.update()
        pygame.draw.rect(
            self.screen,
            (0, 200, 255),
            (self.rect.x + camera.x, self.rect.y + camera.y,
             self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            (self.rect.x + camera.x, self.rect.y + camera.y,
             self.rect.width, self.rect.height),
            2,
        )
