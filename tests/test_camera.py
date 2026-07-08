import pygame

from classes.Camera import Camera, FOLLOW_OFFSET_TILES


class FakeLevel:
    levelLength = 100


class FakeEntity:
    def __init__(self, tile_x):
        self.rect = pygame.Rect(int(tile_x * 32), 384, 32, 32)
        self.levelObj = FakeLevel()

    def getPosIndexAsFloat(self):
        class V:
            pass
        v = V()
        v.x = self.rect.x / 32.0
        v.y = self.rect.y / 32.0
        return v


def make(tile_x):
    ent = FakeEntity(tile_x)
    cam = Camera(pygame.Rect(0, 0, 32, 32), ent)
    return cam, ent


def test_left_edge_clamps_to_zero():
    cam, _ = make(2)
    cam.snap()
    assert cam.pos.x == 0
    assert cam.x == 0


def test_follow_keeps_player_at_offset():
    cam, _ = make(40)
    cam.snap()
    assert cam.pos.x == -40 + FOLLOW_OFFSET_TILES


def test_right_edge_clamps():
    cam, _ = make(99)
    cam.snap()
    # right_limit = 100 - 10 = 90
    assert cam.pos.x == -90 + FOLLOW_OFFSET_TILES


def test_move_converges_smoothly_to_target():
    cam, ent = make(2)
    cam.snap()
    ent.rect.x = 50 * 32  # teleporta o jogador
    cam.move()
    first_step = cam.pos.x
    assert first_step != 0            # comecou a se mover
    assert first_step > -40           # mas nao chegou de uma vez
    for _ in range(200):
        cam.move()
    assert abs(cam.pos.x - (-50 + FOLLOW_OFFSET_TILES)) < 0.02


def test_snap_skips_interpolation():
    cam, ent = make(2)
    ent.rect.x = 50 * 32
    cam.snap()
    assert cam.pos.x == -50 + FOLLOW_OFFSET_TILES
