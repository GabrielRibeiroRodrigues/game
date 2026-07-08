class JumpTrait:
    def __init__(self, entity):
        self.verticalSpeed = -12
        self.jumpHeight = 120
        self.entity = entity
        self.initalHeight = 384
        self.deaccelerationHeight = self.jumpHeight - ((self.verticalSpeed*self.verticalSpeed)/(2*self.entity.gravity))
        self.jumpCount = 0
        self.maxJumps = 2
        self.wasJumping = False

    def jump(self, jumping):
        # Reset jump count when landing. Precisa rodar ANTES de processar um
        # pulo novo neste frame: um pulo do chao seta jumpCount=1, mas
        # onGround so vira False depois (via fisica/colisao no proximo
        # frame) - se esse reset rodasse no fim da funcao como antes, ele
        # zerava de volta o jumpCount=1 na mesma chamada, e o jogo "esquecia"
        # que o pulo do chao ja tinha sido usado, permitindo pulo triplo
        # (chao + 2 no ar) em vez de duplo (chao + 1 no ar).
        if self.entity.onGround:
            self.jumpCount = 0

        if jumping:
            if not self.wasJumping:
                if self.entity.onGround:
                    # First jump from ground
                    self.jumpCount = 1
                    self.entity.sound.play_sfx(self.entity.sound.jump)
                    self.entity.vel.y = self.verticalSpeed
                    self.entity.inAir = True
                    self.initalHeight = self.entity.rect.y
                    self.entity.inJump = True
                    self.entity.obeyGravity = False
                elif self.jumpCount < self.maxJumps:
                    # Double jump in the air
                    self.jumpCount += 1
                    self.entity.sound.play_sfx(self.entity.sound.jump)
                    self.entity.vel.y = self.verticalSpeed * 0.85
                    self.entity.inAir = True
                    self.initalHeight = self.entity.rect.y
                    self.entity.inJump = True
                    self.entity.obeyGravity = False
            self.wasJumping = True
        else:
            self.wasJumping = False

        if self.entity.inJump:
            if (self.initalHeight-self.entity.rect.y) >= self.deaccelerationHeight or self.entity.vel.y == 0:
                self.entity.inJump = False
                self.entity.obeyGravity = True

    def reset(self):
        self.entity.inAir = False
        self.jumpCount = 0
