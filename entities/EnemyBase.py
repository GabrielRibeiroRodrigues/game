"""Base compartilhada dos inimigos comuns (Drone, HeavyBot, Sentry).

Centraliza o ciclo de vida que era triplicado: fisica basica, hit-stun com
knockback decadente e flash, e morte com pontos + FX. Subclasses definem:

- POINTS / DEATH_COLOR / DEATH_FX_OFFSET / FLOAT_TEXT_OFFSET (tunables)
- _behave(camera): comportamento por frame quando vivo e sem stun
  (deve mover e desenhar a entidade)
- _draw(camera, flash): renderizacao
- _onDead(camera): animacao de corpo (default: remover imediatamente)

O chefe (Boss) nao herda daqui: ele tem regras proprias de dano/stun.
"""
import pygame

from core import config
from core import fx as FX
from classes.Collider import Collider
from entities.EntityBase import EntityBase


class EnemyBase(EntityBase):
    POINTS = 100
    DEATH_COLOR = (255, 255, 255)
    DEATH_FX_OFFSET = 0     # deslocamento Y da explosao de morte
    FLOAT_TEXT_OFFSET = 0   # deslocamento Y do texto de pontos

    def __init__(self, screen, x, y, level, sound, dashboard) -> None:
        super().__init__(x, y - 1, config.ENEMY_GRAVITY)
        self.screen = screen
        self.levelObj = level
        self.sound = sound
        self.dashboard = dashboard
        self.collision = Collider(self, level)
        self.type = "Mob"

    # ---------- ciclo de vida ----------

    def update(self, camera) -> None:
        if self.alive is None:
            return
        if not self.alive:
            self._onDead(camera)
            return
        self.applyGravity()
        if self.hit_stun > 0:
            self._run_hit_stun(camera)
            return
        self._behave(camera)

    def _run_hit_stun(self, camera) -> None:
        self.hit_stun -= 1
        self.rect.y += int(self.vel.y)
        self.collision.checkY()
        self.rect.x += int(self.knockback_vel)
        self.knockback_vel *= 0.8
        if self.hit_stun == 0 and self.hp <= 0:
            self._die()
        self._draw(camera, flash=(self.hit_stun // 2) % 2 == 0)

    def _die(self) -> None:
        self.alive = False
        self.timer = 0
        self.dashboard.points += self.POINTS
        FX.explosion(self.rect.centerx,
                     self.rect.centery + self.DEATH_FX_OFFSET,
                     self.DEATH_COLOR)
        FX.float_text(str(self.POINTS), self.rect.x + 3,
                      self.rect.y + self.FLOAT_TEXT_OFFSET)
        FX.shake(6, 3)

    # ---------- hooks ----------

    def _behave(self, camera) -> None:
        raise NotImplementedError

    def _draw(self, camera, flash: bool = False) -> None:
        raise NotImplementedError

    def _onDead(self, camera) -> None:
        self.alive = None

    # ---------- util ----------

    @staticmethod
    def flash_image(image: pygame.Surface) -> pygame.Surface:
        """Copia do sprite clareada para o flash de hit (preserva alpha)."""
        image = image.convert_alpha()
        image.fill((180, 180, 180), special_flags=pygame.BLEND_RGB_ADD)
        return image
