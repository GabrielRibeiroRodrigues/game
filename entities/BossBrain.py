"""Maquina de estados do Mega Bot, pura (sem pygame) para ser testavel.

Estados: idle -> telegraph_charge -> charge -> stunned -> idle
               -> telegraph_jump  -> jump   -> (slam) -> idle
         dying -> dead (via take_hit)
Eventos retornados por tick(): charge_start, wall_impact, jump_start,
slam, died, ou None."""

MAX_HP = 12
TELEGRAPH_FRAMES = 30
STUN_FRAMES = 45
DYING_FRAMES = 90


class BossBrain:
    def __init__(self):
        self.state = "idle"
        self.timer = 60
        self.hp = MAX_HP
        self.max_hp = MAX_HP
        self.enraged = False
        self._summon_pending = False
        self.next_attack = "charge"
        self.facing = -1

    def idle_duration(self):
        return 30 if self.enraged else 60

    def charge_speed(self):
        return 7 if self.enraged else 5

    def take_hit(self, damage):
        if self.state in ("dying", "dead"):
            return
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.state = "dying"
            self.timer = DYING_FRAMES
        elif self.hp <= self.max_hp // 2 and not self.enraged:
            self.enraged = True
            self._summon_pending = True

    def should_summon(self):
        if self._summon_pending and self.state != "dying":
            self._summon_pending = False
            return True
        return False

    def tick(self, player_dx, hit_wall, on_ground):
        event = None
        if self.state == "idle":
            if player_dx != 0:
                self.facing = 1 if player_dx > 0 else -1
            self.timer -= 1
            if self.timer <= 0:
                if self.next_attack == "charge":
                    self.state = "telegraph_charge"
                    self.next_attack = "jump"
                else:
                    self.state = "telegraph_jump"
                    self.next_attack = "charge"
                self.timer = TELEGRAPH_FRAMES
        elif self.state == "telegraph_charge":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "charge"
                event = "charge_start"
        elif self.state == "charge":
            if hit_wall:
                self.state = "stunned"
                self.timer = STUN_FRAMES
                event = "wall_impact"
        elif self.state == "stunned":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "idle"
                self.timer = self.idle_duration()
        elif self.state == "telegraph_jump":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "jump"
                event = "jump_start"
        elif self.state == "jump":
            if on_ground:
                self.state = "idle"
                self.timer = self.idle_duration()
                event = "slam"
        elif self.state == "dying":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "dead"
                event = "died"
        return event
