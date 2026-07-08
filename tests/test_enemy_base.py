from core import fx as FX
from entities.EnemyBase import EnemyBase


class FakeTile:
    rect = None


class FakeLevel:
    def __init__(self):
        self.level = [[FakeTile() for _ in range(20)] for _ in range(20)]
        self.levelLength = 20


class FakeDashboard:
    points = 0


class FakeCam:
    x = 0
    entity = None


class StubEnemy(EnemyBase):
    POINTS = 150

    def __init__(self):
        super().__init__(None, 2, 2, FakeLevel(), None, FakeDashboard())
        self.hp = 1
        self.max_hp = 1
        self.behaved = 0
        self.drawn = 0

    def _behave(self, camera):
        self.behaved += 1

    def _draw(self, camera, flash=False):
        self.drawn += 1


def setup_function(_):
    FX.reset()


def test_on_hit_sets_stun_and_knockback():
    e = StubEnemy()
    e.on_hit(1, damage=1, knockback=4, pop=-2)
    assert e.hit_stun == 20
    assert e.knockback_vel == 4
    assert e.vel.y == -2


def test_hit_stun_then_death_awards_points_once():
    e = StubEnemy()
    e.on_hit(1, damage=1)
    for _ in range(20):
        e.update(FakeCam())
    assert e.alive is False
    assert e.dashboard.points == 150
    e.update(FakeCam())  # _onDead default remove imediatamente
    assert e.alive is None
    e.update(FakeCam())  # nao premia de novo
    assert e.dashboard.points == 150


def test_survivor_returns_to_behavior_after_stun():
    e = StubEnemy()
    e.hp = 2
    e.on_hit(1, damage=1)
    for _ in range(20):
        e.update(FakeCam())
    assert e.alive is True
    assert e.hp == 1
    e.update(FakeCam())
    assert e.behaved == 1


def test_behave_runs_every_frame_without_stun():
    e = StubEnemy()
    e.update(FakeCam())
    e.update(FakeCam())
    assert e.behaved == 2
    assert e.hit_stun == 0
