import random

from classes.Collider import Collider


class LeftRightWalkTrait:
    def __init__(self, entity, level):
        self.direction = random.choice([-1, 1])
        self.entity = entity
        self.collDetection = Collider(self.entity, level)
        self.speed = 1
        self.entity.vel.x = self.speed * self.direction

    def update(self):
        if self.entity.vel.x == 0 or self._isCliffAhead():
            self.direction *= -1
        self.entity.vel.x = self.speed * self.direction
        self.moveEntity()

    def _isCliffAhead(self):
        if not self.entity.onGround:
            return False
        level = self.collDetection.level
        check_col = self.entity.getPosIndex().x + (1 if self.direction == 1 else -1)
        foot_row = self.entity.rect.bottom // 32
        try:
            return level[foot_row][check_col].rect is None
        except IndexError:
            return True

    def moveEntity(self):
        self.entity.rect.y += self.entity.vel.y
        self.collDetection.checkY()
        self.entity.rect.x += self.entity.vel.x
        self.collDetection.checkX()
