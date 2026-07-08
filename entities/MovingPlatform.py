import pygame

from core.log import get_logger

log = get_logger(__name__)


class MovingPlatform:
    def __init__(self, x, y, level, screen, direction="horizontal", amplitude=3, speed=1):
        # x, y in TILE coords (multiply by 32 for pixels)
        # direction: "horizontal" or "vertical"
        # amplitude: tiles to move (e.g. 3 = moves 3 tiles left/right)
        # speed: pixels per frame (e.g. 1.5)
        self.alive = True
        self.type = "Platform"
        self.rect = pygame.Rect(x * 32, y * 32, 64, 16)  # 2 tiles wide, half tile tall platform
        self.screen = screen
        self.level = level
        self.direction = direction
        self.amplitude = amplitude * 32  # convert to pixels
        self.speed = speed
        self.startX = x * 32
        self.startY = y * 32
        self.vel = speed  # current velocity, flips when reaching amplitude
        # posicao real em float: o rect do pygame arredonda para int a cada
        # atribuicao, entao reler self.rect.x/y como base do proximo passo
        # (em vez de manter um acumulador float) faz o erro de arredondamento
        # se acumular e a plataforma andar mais rapido que "speed". delta_x/y
        # guarda o quanto o rect realmente andou no frame, para o jogador
        # "montado" andar exatamente o mesmo tanto (ver Level.updateEntities).
        self.posX = float(self.startX)
        self.posY = float(self.startY)
        self.delta_x = 0
        self.delta_y = 0
        self.image = self._loadSprite()

    def _loadSprite(self):
        try:
            sheet = pygame.image.load("./img/tiles.png").convert()
            tile = pygame.Surface((16, 16))
            tile.blit(sheet, (0, 0), pygame.Rect(4 * 16, 4 * 16, 16, 16))
            return pygame.transform.scale(tile, (64, 16))
        except (pygame.error, FileNotFoundError) as exc:
            log.warning("tiles.png indisponivel (%s); usando fallback solido", exc)
            surf = pygame.Surface((64, 16))
            surf.fill((82, 96, 124))  # stone gray color
            return surf

    def update(self, camera):
        if self.direction == "horizontal":
            old_x = self.rect.x
            self.posX, self.vel = self._clamp(
                self.posX, self.startX, self.vel, self.amplitude
            )
            self.rect.x = round(self.posX)
            self.delta_x = self.rect.x - old_x
            self.delta_y = 0
        else:
            old_y = self.rect.y
            self.posY, self.vel = self._clamp(
                self.posY, self.startY, self.vel, self.amplitude
            )
            self.rect.y = round(self.posY)
            self.delta_y = self.rect.y - old_y
            self.delta_x = 0
        self.draw(camera)

    @staticmethod
    def _clamp(pos, start, vel, amplitude):
        """Move pos por vel e garante que nao ultrapasse start±amplitude."""
        new_pos = pos + vel
        new_vel = vel
        if abs(new_pos - start) >= amplitude:
            new_vel = -vel
            new_pos = start + amplitude * (1 if new_pos > start else -1)
        return new_pos, new_vel

    def draw(self, camera):
        drawX = self.rect.x + camera.x
        drawY = self.rect.y + camera.y
        self.screen.blit(self.image, (drawX, drawY))
