"""Regras puras de combate da jogadora (testaveis sem pygame display)."""

INVULN_FRAMES = 90


def is_stomp(player_vel_y, player_bottom, mob_rect):
    """Stomp = jogadora caindo com os pes acima do centro vertical do mob."""
    return player_vel_y > 0 and player_bottom <= mob_rect.centery


def apply_damage(hearts, invincibility_frames):
    """Retorna (hearts, invincibility_frames, dano_aplicado)."""
    if invincibility_frames > 0:
        return hearts, invincibility_frames, False
    return hearts - 1, INVULN_FRAMES, True
