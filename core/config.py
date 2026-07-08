"""Configuracao central do Crazy World.

Constantes globais do jogo em um unico lugar. Tunables especificos de uma
classe (ex.: timings do combo em MeleeTrait, estados do chefe em BossBrain)
permanecem como constantes de classe, junto do codigo que os usa — isso
tambem e centralizacao, no escopo certo.

Fisica: o jogo usa timestep FIXO de 60 Hz (velocidades em pixels/frame).
Decisao deliberada — determinismo e o padrao de platformers 2D; toda a
fisica e combate testados dependem desse passo. FPS abaixo, portanto, e
tanto o limite de render quanto o passo de simulacao.
"""
from typing import Final, Tuple

# --- janela / render ---
TILE_SIZE: Final[int] = 32
INTERNAL_SIZE: Final[Tuple[int, int]] = (640, 480)
WINDOW_SCALE: Final[int] = 2
FPS: Final[int] = 60

# --- fisica / jogador ---
PLAYER_GRAVITY: Final[float] = 0.8
ENEMY_GRAVITY: Final[float] = 1.25
PLAYER_MAX_HEARTS: Final[int] = 3
POWERUP_DURATION_FRAMES: Final[int] = 600  # 10s a 60fps

# --- arquivos ---
SETTINGS_PATH: Final[str] = "./settings.json"
LEVELS_DIR: Final[str] = "./levels"
