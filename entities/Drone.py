"""Drone: inimigo basico que patrulha o chao (1 HP)."""
from classes.Animation import Animation
from entities.EnemyBase import EnemyBase
from traits.leftrightwalk import LeftRightWalkTrait


class Drone(EnemyBase):
    POINTS = 100
    DEATH_COLOR = (120, 220, 255)

    def __init__(self, screen, spriteColl, x, y, level, sound, dashboard):
        super().__init__(screen, x, y, level, sound, dashboard)
        self.spriteCollection = spriteColl
        self.animation = Animation(
            [
                self.spriteCollection.get("drone-1").image,
                self.spriteCollection.get("drone-2").image,
            ]
        )
        self.leftrightTrait = LeftRightWalkTrait(self, level)
        self.hp = 1
        self.max_hp = 1

    def _behave(self, camera):
        self.leftrightTrait.update()
        self._draw(camera)
        self.animation.update()

    def _draw(self, camera, flash=False):
        image = self.animation.image
        if flash:
            image = self.flash_image(image)
        self.screen.blit(image, (self.rect.x + camera.x, self.rect.y))

    def _onDead(self, camera):
        if self.timer < self.timeAfterDeath:
            self.screen.blit(
                self.spriteCollection.get("drone-flat").image,
                (self.rect.x + camera.x, self.rect.y),
            )
        else:
            self.alive = None
        self.timer += 0.1
