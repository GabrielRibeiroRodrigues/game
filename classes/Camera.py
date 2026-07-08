"""Camera com follow suave (lerp exponencial) e limites do nivel.

O alvo mantem o jogador a FOLLOW_OFFSET_TILES da borda esquerda da tela,
com clamp nas bordas do nivel; a posicao real persegue o alvo a
SMOOTHING por frame (timestep fixo de 60 Hz). snap() corta a interpolacao
(usado em spawn/respawn para nao "panoramicar" ate o checkpoint).
"""
from classes.Maths import Vec2D
from core import config

FOLLOW_OFFSET_TILES = 10.0   # distancia do jogador a borda esquerda
RIGHT_MARGIN_TILES = 10.0    # margem da borda direita do nivel
SMOOTHING = 0.15             # fracao da distancia percorrida por frame
SNAP_EPSILON = 0.01          # em tiles: abaixo disso cola no alvo


class Camera:
    def __init__(self, pos, entity) -> None:
        self.pos = Vec2D(pos.x, pos.y)
        self.entity = entity
        self.x = self.pos.x * config.TILE_SIZE
        self.y = self.pos.y * config.TILE_SIZE

    def _target_x(self) -> float:
        """Posicao-alvo da camera em tiles (negativa: desloca o mundo)."""
        player_x = self.entity.getPosIndexAsFloat().x
        level_length = getattr(
            getattr(self.entity, "levelObj", None), "levelLength", 60
        )
        right_limit = max(50.0, level_length - RIGHT_MARGIN_TILES)
        clamped = min(max(player_x, FOLLOW_OFFSET_TILES), right_limit)
        return -clamped + FOLLOW_OFFSET_TILES

    def move(self) -> None:
        target = self._target_x()
        self.pos.x += (target - self.pos.x) * SMOOTHING
        if abs(target - self.pos.x) < SNAP_EPSILON:
            self.pos.x = target
        self.x = self.pos.x * config.TILE_SIZE
        self.y = self.pos.y * config.TILE_SIZE

    def snap(self) -> None:
        """Vai direto ao alvo, sem interpolacao (spawn/teleporte)."""
        self.pos.x = self._target_x()
        self.x = self.pos.x * config.TILE_SIZE
        self.y = self.pos.y * config.TILE_SIZE
