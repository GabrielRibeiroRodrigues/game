from core import fx as FX


def setup_function(_):
    FX.reset()


def test_hitstop_accumulates_max_not_sum():
    FX.hitstop(3)
    FX.hitstop(5)
    assert FX._hitstop == 5  # max, nao soma
    FX.hitstop(2)
    assert FX._hitstop == 5


def test_hitstop_tick():
    FX.hitstop(2)
    assert FX.hitstop_active()
    FX.tick_hitstop()
    FX.tick_hitstop()
    assert not FX.hitstop_active()


def test_shake_offset_zero_when_inactive():
    assert FX.get_shake_offset() == (0, 0)


def test_shake_decays_via_update():
    FX.shake(3, 4)
    off = FX.get_shake_offset()
    assert -4 <= off[0] <= 4 and -4 <= off[1] <= 4
    FX.update()
    FX.update()
    FX.update()
    assert FX.get_shake_offset() == (0, 0)


def test_particles_expire():
    FX.explosion(100, 100, (255, 0, 0))
    assert len(FX._particles) > 0
    for _ in range(200):
        FX.update()
    assert len(FX._particles) == 0


def test_float_text_expires():
    FX.float_text("100", 50, 50)
    assert len(FX._texts) == 1
    for _ in range(60):
        FX.update()
    assert len(FX._texts) == 0


def test_fade_in_reaches_zero():
    FX.fade_in(10)
    assert FX._fade_alpha == 255
    for _ in range(10):
        FX.update()
    assert FX._fade_alpha == 0


def test_fade_in_zero_frames_does_not_crash():
    FX.fade_in(0)
    FX.update()
    assert FX._fade_alpha == 0


def test_banner_expires():
    FX.phase_banner("FASE 1")
    assert FX._banner is not None
    for _ in range(FX.BANNER_TOTAL + 1):
        FX.update()
    assert FX._banner is None


def test_reset_clears_everything():
    FX.explosion(0, 0, (255, 0, 0))
    FX.float_text("x", 0, 0)
    FX.shake(10, 5)
    FX.hitstop(10)
    FX.phase_banner("X")
    FX.fade_in(30)
    FX.reset()
    assert FX._particles == [] and FX._texts == []
    assert FX.get_shake_offset() == (0, 0)
    assert not FX.hitstop_active()
    assert FX._banner is None and FX._fade_alpha == 0
