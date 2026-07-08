import pygame

from classes.CombatRules import is_stomp, apply_damage


def test_stomp_when_falling_and_above():
    mob = pygame.Rect(100, 100, 32, 32)
    # jogadora caindo, pes acima do centro do mob
    assert is_stomp(player_vel_y=4, player_bottom=108, mob_rect=mob)


def test_no_stomp_when_rising():
    mob = pygame.Rect(100, 100, 32, 32)
    assert not is_stomp(player_vel_y=-4, player_bottom=108, mob_rect=mob)


def test_no_stomp_when_side_hit():
    mob = pygame.Rect(100, 100, 32, 32)
    # pes abaixo do centro do mob = colisao lateral
    assert not is_stomp(player_vel_y=4, player_bottom=130, mob_rect=mob)


def test_apply_damage_decrements_and_grants_invuln():
    hearts, invuln, applied = apply_damage(hearts=3, invincibility_frames=0)
    assert (hearts, invuln, applied) == (2, 90, True)


def test_apply_damage_blocked_by_invuln():
    hearts, invuln, applied = apply_damage(hearts=3, invincibility_frames=30)
    assert (hearts, invuln, applied) == (3, 30, False)


def test_apply_damage_can_reach_zero():
    hearts, invuln, applied = apply_damage(hearts=1, invincibility_frames=0)
    assert hearts == 0 and applied
