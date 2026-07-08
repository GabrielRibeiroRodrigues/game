import pygame

from core import config

from classes.Maths import Vec2D


class EntityBase(object):
    def __init__(self, x, y, gravity):
        self.vel = Vec2D()
        tile = config.TILE_SIZE
        self.rect = pygame.Rect(x * tile, y * tile, tile, tile)
        self.gravity = gravity
        self.traits = None
        self.alive = True
        self.active = True
        self.bouncing = False
        self.timeAfterDeath = 5
        self.timer = 0
        self.type = ""
        self.onGround = False
        self.obeyGravity = True
        self.hp = 1
        self.max_hp = 1
        self.hit_stun = 0
        self.knockback_vel = 0

    def on_hit(self, direction, damage=1, knockback=4, pop=-2):
        """direction: 1=direita, -1=esquerda (knockback vai nessa direcao)."""
        self.hp -= damage
        self.hit_stun = 20
        self.knockback_vel = direction * knockback
        self.vel.y = pop

    def applyGravity(self):
        if self.obeyGravity:
            self.vel.y += self.gravity

    def updateTraits(self):
        for trait in self.traits.values():
            try:
                trait.update()
            except AttributeError:
                pass

    def getPosIndex(self):
        return Vec2D(self.rect.x // config.TILE_SIZE, self.rect.y // config.TILE_SIZE)

    def getPosIndexAsFloat(self):
        return Vec2D(self.rect.x / float(config.TILE_SIZE),
                     self.rect.y / float(config.TILE_SIZE))
