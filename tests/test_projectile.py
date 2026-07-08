import pygame

from entities.Projectile import Projectile


class FakeCam:
    x = 0
    y = 0


class FakeMob:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.alive = True
        self.type = "Mob"
        self.hits = []

    def on_hit(self, direction, damage=1, knockback=4, pop=-2):
        self.hits.append(damage)


def test_player_projectile_one_shots_mob():
    mob = FakeMob(120, 100)
    # x=110: apos 1 update (speed 7) o rect 117..129 sobrepoe o mob em 120
    p = Projectile(110, 108, 1, screen=None, owner="player")
    p.update(FakeCam(), [mob])
    assert not p.alive
    assert mob.hits == [99]


def test_enemy_projectile_ignores_mobs():
    mob = FakeMob(120, 100)
    p = Projectile(100, 108, 1, screen=None, owner="enemy", speed=3)
    for _ in range(20):
        p.update(FakeCam(), [mob])
    assert mob.hits == []
    assert p.alive


def test_projectile_expires():
    p = Projectile(0, 0, 1, screen=None)
    for _ in range(p.lifetime + 1):
        p.update(FakeCam(), [])
    assert not p.alive


def test_projectile_dies_on_solid_tile():
    class FakeTile:
        rect = pygame.Rect(160, 96, 32, 32)

    class FakeLevelObj:
        level = [[FakeTile() for _ in range(10)] for _ in range(10)]

    p = Projectile(140, 100, 1, screen=None, level=FakeLevelObj())
    for _ in range(5):
        p.update(FakeCam(), [])
    assert not p.alive


def test_projectile_dies_past_left_edge():
    class FakeTile:
        rect = None

    class FakeLevelObj:
        level = [[FakeTile() for _ in range(10)] for _ in range(10)]

    p = Projectile(4, 100, -1, screen=None, level=FakeLevelObj())
    for _ in range(3):
        p.update(FakeCam(), [])
    assert not p.alive
