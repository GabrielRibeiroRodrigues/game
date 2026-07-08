import pygame

from traits.melee import MeleeTrait


class FakeGo:
    heading = 1


class FakeEntity:
    def __init__(self):
        self.rect = pygame.Rect(100, 100, 32, 32)
        self.traits = {"goTrait": FakeGo()}


def make():
    return MeleeTrait(FakeEntity())


def run_frames(m, n):
    for _ in range(n):
        m.update()


def test_first_attack_starts_stage_1():
    m = make()
    m.trigger()
    assert m.combo_stage == 1
    assert m.is_attacking


def test_chain_within_window_advances_stage():
    m = make()
    m.trigger()
    run_frames(m, MeleeTrait.ATTACK_DURATION)  # fim do golpe 1
    assert not m.is_attacking
    m.trigger()  # dentro da janela
    assert m.combo_stage == 2
    run_frames(m, MeleeTrait.ATTACK_DURATION)
    m.trigger()
    assert m.combo_stage == 3


def test_queued_input_during_swing_chains():
    m = make()
    m.trigger()
    run_frames(m, 3)
    m.trigger()  # buffer no meio do golpe
    run_frames(m, MeleeTrait.ATTACK_DURATION - 3)
    assert m.combo_stage == 2
    assert m.is_attacking


def test_missed_window_goes_to_cooldown():
    m = make()
    m.trigger()
    run_frames(m, MeleeTrait.ATTACK_DURATION + MeleeTrait.CHAIN_WINDOW)
    assert m.cooldown > 0
    m.trigger()  # ignorado durante cooldown
    assert not m.is_attacking


def test_stage3_enters_cooldown_and_resets():
    m = make()
    for _ in range(3):
        m.trigger()
        run_frames(m, MeleeTrait.ATTACK_DURATION)
    assert m.cooldown == MeleeTrait.COOLDOWN
    run_frames(m, MeleeTrait.COOLDOWN)
    assert m.combo_stage == 0
    m.trigger()
    assert m.combo_stage == 1


def test_damage_and_knockback_per_stage():
    m = make()
    m.combo_stage = 1
    assert m.current_damage() == 1 and m.current_knockback() == 4
    m.combo_stage = 3
    assert m.current_damage() == 2 and m.current_knockback() == 8


def test_hitbox_only_while_attacking_and_follows_heading():
    m = make()
    assert m.get_hitbox() is None
    m.trigger()
    hb = m.get_hitbox()
    assert hb is not None and hb.left == m.entity.rect.right
    m.entity.traits["goTrait"].heading = -1
    hb = m.get_hitbox()
    assert hb.right == m.entity.rect.left


def test_hit_entities_reset_each_swing():
    m = make()
    m.trigger()
    m.hit_entities.add("enemy_a")
    run_frames(m, MeleeTrait.ATTACK_DURATION)
    m.trigger()
    assert m.hit_entities == set()
