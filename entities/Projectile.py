import pygame

from core import fx as FX


class Projectile:
    def __init__(self, x, y, direction, screen, owner="player",
                 speed=7, color=(255, 80, 0), level=None):
        self.rect = pygame.Rect(x, y, 12, 8)
        self.screen = screen
        self.direction = direction
        self.speed = speed
        self.color = color
        self.owner = owner
        self.level = level  # objeto Level (atributo .level e a grade de tiles)
        self.alive = True
        self.type = "Projectile"
        self.lifetime = 90 if owner == "player" else 240

    def _hits_solid_tile(self):
        if self.level is None:
            return False
        col = self.rect.centerx // 32
        row = self.rect.centery // 32
        if col < 0 or row < 0:
            return True
        try:
            tile = self.level.level[row][col]
        except IndexError:
            return True
        return tile.rect is not None

    def update(self, camera, entityList):
        if not self.alive:
            return
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            return
        self.rect.x += self.direction * self.speed
        if self._hits_solid_tile():
            self.alive = False
            return
        if self.owner == "player":
            for entity in entityList:
                if entity.alive and entity.alive is not None and entity.type == "Mob":
                    if self.rect.colliderect(entity.rect):
                        entity.on_hit(self.direction, damage=99, knockback=6)
                        self.alive = False
                        return
            FX.trail(self.rect.centerx, self.rect.centery)
        if self.screen is not None:
            pygame.draw.ellipse(
                self.screen,
                self.color,
                (self.rect.x + camera.x, self.rect.y + camera.y,
                 self.rect.width, self.rect.height),
            )
