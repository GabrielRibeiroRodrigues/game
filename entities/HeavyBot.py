"""HeavyBot: inimigo blindado que patrulha o chao (2 HP, sprite alto)."""
import pygame

from classes.Animation import Animation
from entities.EnemyBase import EnemyBase
from traits.leftrightwalk import LeftRightWalkTrait


class HeavyBot(EnemyBase):
    POINTS = 200
    DEATH_COLOR = (255, 160, 60)
    DEATH_FX_OFFSET = -16
    FLOAT_TEXT_OFFSET = -32

    def __init__(self, screen, spriteColl, x, y, level, sound, dashboard):
        super().__init__(screen, x, y, level, sound, dashboard)
        self.spriteCollection = spriteColl
        self.animation = Animation(
            [
                self.spriteCollection.get("heavybot-1").image,
                self.spriteCollection.get("heavybot-2").image,
            ]
        )
        self.leftrightTrait = LeftRightWalkTrait(self, level)
        self.hp = 2
        self.max_hp = 2

    def _behave(self, camera):
        self.leftrightTrait.update()
        self._draw(camera)
        self.animation.update()

    def _draw(self, camera, flash=False):
        key = "heavybot-1" if self.hp >= 2 else "heavybot-damaged"
        frame = self.spriteCollection.get(key).image
        if self.leftrightTrait.direction == 1:
            frame = pygame.transform.flip(frame, True, False)
        if flash:
            frame = self.flash_image(frame)
        self.screen.blit(frame, (self.rect.x + camera.x, self.rect.y - 32))

    def _onDead(self, camera):
        if self.timer < self.timeAfterDeath:
            frame = self.spriteCollection.get("heavybot-damaged").image
            self.screen.blit(frame, (self.rect.x + camera.x, self.rect.y - 32))
        else:
            self.alive = None
        self.timer += 0.1
