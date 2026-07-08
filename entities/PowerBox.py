from entities.EntityBase import EntityBase


class PowerBox(EntityBase):
    def __init__(self, screen, x, y, sound, dashboard, level, spriteColl, gravity=0):
        super().__init__(x, y, gravity)
        self.screen = screen
        self.type = "Block"
        self.triggered = False
        self.spawned = False
        self.time = 0
        self.maxTime = 10
        self.sound = sound
        self.dashboard = dashboard
        self.level = level
        self.vel_anim = 1
        self.idle_image = spriteColl.get("powerbox_idle").image
        self.depleted_image = spriteColl.get("powerbox_depleted").image

    def update(self, cam):
        if self.triggered:
            if not self.spawned:
                self.level.addWeaponPowerup(self.rect.x // 32, self.rect.y // 32 - 1)
                self.spawned = True
            if self.time < self.maxTime:
                self.time += 1
                self.rect.y -= self.vel_anim
            elif self.time < self.maxTime * 2:
                self.time += 1
                self.rect.y += self.vel_anim

        self._draw(cam)

    def _draw(self, cam):
        dx = self.rect.x + cam.x
        dy = self.rect.y
        image = self.depleted_image if self.triggered else self.idle_image
        self.screen.blit(image, (dx, dy))
