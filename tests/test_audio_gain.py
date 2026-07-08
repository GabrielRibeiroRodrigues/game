from core.audio import volume_to_gain, MAX_VOLUME, GAIN_PER_UNIT


def test_default_volume_matches_historic_gain():
    # volume 5 deve reproduzir o ganho historico de 0.2
    assert abs(volume_to_gain(5) - 0.2) < 1e-9


def test_gain_clamps_below_zero():
    assert volume_to_gain(-3) == 0.0


def test_gain_clamps_above_max():
    assert volume_to_gain(99) == MAX_VOLUME * GAIN_PER_UNIT


def test_zero_is_silent():
    assert volume_to_gain(0) == 0.0
