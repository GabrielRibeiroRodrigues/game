import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from entities.MovingPlatform import MovingPlatform


def test_clamp_sem_overshoot_direita():
    """Plataforma que vai ultrapassar o limite deve ser clamped e inverter vel."""
    pos, vel = MovingPlatform._clamp(95, start=0, vel=10, amplitude=100)
    assert pos == 100   # clamped no limite exato
    assert vel == -10   # velocidade invertida


def test_clamp_sem_overshoot_esquerda():
    pos, vel = MovingPlatform._clamp(-95, start=0, vel=-10, amplitude=100)
    assert pos == -100
    assert vel == 10


def test_clamp_movimento_normal():
    """Dentro do limite: sem clamp, vel inalterada."""
    pos, vel = MovingPlatform._clamp(50, start=0, vel=10, amplitude=100)
    assert pos == 60
    assert vel == 10


def test_clamp_no_limite_exato():
    """Exatamente no limite: inverte mas não move além."""
    pos, vel = MovingPlatform._clamp(90, start=0, vel=10, amplitude=100)
    assert pos == 100
    assert vel == -10
