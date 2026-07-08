import pygame


class MeleeTrait:
    ATTACK_DURATION = 8
    CHAIN_WINDOW = 14
    COOLDOWN = 20

    def __init__(self, entity):
        self.entity = entity
        self.combo_stage = 0      # 0=idle, 1..3 = golpe atual/ultimo golpe dado
        self.attack_timer = 0     # frames restantes do golpe ativo
        self.chain_timer = 0      # janela para encadear o proximo golpe
        self.cooldown = 0
        self.queued = False       # input bufferizado durante um golpe
        self.hit_entities = set()  # entidades ja atingidas pelo golpe atual

    @property
    def is_attacking(self):
        return self.attack_timer > 0

    def trigger(self):
        if self.cooldown > 0:
            return
        if self.attack_timer > 0:
            if self.combo_stage < 3:
                self.queued = True
            return
        if self.chain_timer > 0 and 0 < self.combo_stage < 3:
            self._start(self.combo_stage + 1)
        else:
            self._start(1)

    def _start(self, stage):
        self.combo_stage = stage
        self.attack_timer = self.ATTACK_DURATION
        self.chain_timer = 0
        self.queued = False
        self.hit_entities = set()

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
            if self.cooldown == 0:
                self.combo_stage = 0
            return
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                if self.combo_stage >= 3:
                    self.cooldown = self.COOLDOWN
                elif self.queued:
                    self._start(self.combo_stage + 1)
                else:
                    self.chain_timer = self.CHAIN_WINDOW
            return
        if self.chain_timer > 0:
            self.chain_timer -= 1
            if self.chain_timer == 0:
                self.cooldown = self.COOLDOWN

    def current_damage(self):
        return 2 if self.combo_stage == 3 else 1

    def current_knockback(self):
        return 8 if self.combo_stage == 3 else 4

    def current_pop(self):
        return -4 if self.combo_stage == 3 else -2

    def get_hitbox(self):
        if not self.is_attacking:
            return None
        r = self.entity.rect
        heading = self.entity.traits["goTrait"].heading
        if heading == 1:
            return pygame.Rect(r.right, r.top + 4, 28, 24)
        else:
            return pygame.Rect(r.left - 28, r.top + 4, 28, 24)
