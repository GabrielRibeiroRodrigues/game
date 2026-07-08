"""Sentry: torreta estacionaria que telegrafa e atira no jogador (2 HP)."""
import pygame

from entities.EnemyBase import EnemyBase
from entities.Projectile import Projectile


class Sentry(EnemyBase):
    POINTS = 200
    DEATH_COLOR = (255, 90, 90)

    RANGE_X = 8 * 32
    RANGE_Y = 2 * 32
    CHARGE_FRAMES = 45
    COOLDOWN_FRAMES = 75

    def __init__(self, screen, x, y, level, sound, dashboard):
        super().__init__(screen, x, y, level, sound, dashboard)
        self.hp = 2
        self.max_hp = 2
        self.state = "idle"       # idle -> charging -> cooldown
        self.state_timer = 0
        self.facing = -1

    def _behave(self, camera):
        self.rect.y += int(self.vel.y)
        self.collision.checkY()

        player = camera.entity
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        in_range = abs(dx) <= self.RANGE_X and abs(dy) <= self.RANGE_Y
        if dx != 0:
            self.facing = 1 if dx > 0 else -1

        if self.state == "idle":
            if in_range:
                self.state = "charging"
                self.state_timer = self.CHARGE_FRAMES
        elif self.state == "charging":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self._fire()
                self.state = "cooldown"
                self.state_timer = self.COOLDOWN_FRAMES
        elif self.state == "cooldown":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.state = "idle"

        self._draw(camera)

    def _fire(self):
        px = self.rect.centerx + self.facing * 18
        py = self.rect.centery - 4
        self.levelObj.enemy_projectiles.append(
            Projectile(px, py, self.facing, self.screen, owner="enemy",
                       speed=3, color=(255, 60, 60), level=self.levelObj)
        )
        self.sound.play_sfx(self.sound.kick)

    def _draw(self, camera, flash=False):
        x = self.rect.x + camera.x
        y = self.rect.y
        body = (200, 200, 210) if flash else (90, 100, 120)
        dome = (255, 255, 255) if flash else (140, 150, 170)
        # base
        pygame.draw.rect(self.screen, body, (x + 2, y + 18, 28, 14))
        # cupula
        pygame.draw.circle(self.screen, dome, (x + 16, y + 16), 12)
        # canhao
        cx = x + 16 + self.facing * 10
        pygame.draw.rect(
            self.screen, body,
            (min(cx, x + 16), y + 12, abs(cx - (x + 16)) + 6, 6),
        )
        # luz de telegraph: pisca vermelho enquanto carrega
        if self.state == "charging" and (self.state_timer // 4) % 2 == 0:
            pygame.draw.circle(self.screen, (255, 60, 60), (x + 16, y + 10), 4)
        else:
            pygame.draw.circle(self.screen, (60, 220, 120), (x + 16, y + 10), 3)
