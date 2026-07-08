from entities.BossBrain import BossBrain


def tick_n(b, n, **kw):
    events = []
    for _ in range(n):
        ev = b.tick(kw.get("player_dx", 100), kw.get("hit_wall", False),
                    kw.get("on_ground", True))
        if ev:
            events.append(ev)
    return events


def test_starts_idle_then_telegraphs_charge():
    b = BossBrain()
    assert b.state == "idle"
    tick_n(b, 60)
    assert b.state == "telegraph_charge"


def test_charge_flow_until_wall_then_stun():
    b = BossBrain()
    tick_n(b, 60)          # idle -> telegraph_charge
    ev = tick_n(b, 30)     # telegraph -> charge
    assert "charge_start" in ev
    assert b.state == "charge"
    ev = tick_n(b, 1, hit_wall=True)
    assert "wall_impact" in ev
    assert b.state == "stunned"
    tick_n(b, 45)
    assert b.state == "idle"


def test_alternates_charge_and_jump():
    b = BossBrain()
    tick_n(b, 60)
    assert b.state == "telegraph_charge"
    tick_n(b, 30)
    tick_n(b, 1, hit_wall=True)
    tick_n(b, 45)          # stun termina -> idle
    tick_n(b, b.idle_duration())
    assert b.state == "telegraph_jump"


def test_jump_slam_event_on_landing():
    b = BossBrain()
    b.state = "telegraph_jump"
    b.timer = 1
    ev = tick_n(b, 1)
    assert "jump_start" in ev and b.state == "jump"
    ev = tick_n(b, 1, on_ground=False)
    assert ev == [] and b.state == "jump"
    ev = tick_n(b, 1, on_ground=True)
    assert "slam" in ev and b.state == "idle"


def test_enrage_below_half_hp():
    b = BossBrain()
    assert not b.enraged
    b.take_hit(6)
    assert b.enraged
    assert b.idle_duration() == 30
    assert b.charge_speed() == 7
    assert b.should_summon() is True
    assert b.should_summon() is False  # so 1 vez


def test_death_flow():
    b = BossBrain()
    b.take_hit(12)
    assert b.state == "dying"
    ev = tick_n(b, 90)
    assert "died" in ev and b.state == "dead"


def test_no_hits_after_dying():
    b = BossBrain()
    b.take_hit(12)
    hp = b.hp
    b.take_hit(5)
    assert b.hp == hp


def test_facing_tracks_player_in_idle():
    b = BossBrain()
    b.tick(-50, False, True)
    assert b.facing == -1
    b.tick(50, False, True)
    assert b.facing == 1
