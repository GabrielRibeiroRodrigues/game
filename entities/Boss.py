import random

import pygame

from core import config
from core import fx as FX
from entities.BossBrain import BossBrain
from entities.EntityBase import EntityBase
from entities.Projectile import Projectile

JUMP_VEL = -16
SHOCKWAVE_SPEED = 4


STATE_TO_SPRITE = {
    "idle": "idle",
    "telegraph_charge": "telegraph_charge",
    "charge": "charge",
    "stunned": "stunned",
    "telegraph_jump": "telegraph_jump",
    "jump": "jump",
    "dying": "stunned",
    "dead": "stunned",
}


class Boss(EntityBase):
    def __init__(self, screen, x, y, level, sound, dashboard, spriteColl):
        super().__init__(x, y, config.ENEMY_GRAVITY)
        self.rect = pygame.Rect(x * 32, (y - 2) * 32, 64, 64)
        self.screen = screen
        self.levelObj = level
        self.sound = sound
        self.dashboard = dashboard
        self.brain = BossBrain()
        self.images = {
            name: spriteColl.get(f"boss_{name}").image
            for name in STATE_TO_SPRITE.values()
        }
        self.enraged_images = {
            name: spriteColl.get(f"boss_enraged_{name}").image
            for name in set(STATE_TO_SPRITE.values())
        }
        self.type = "Mob"
        self.is_boss = True
        self.hp = self.brain.hp
        self.max_hp = self.brain.max_hp
        self.activated = False
        self.flash_timer = 0
        self.was_airborne = False
        self.jump_dir = 0
        arena_tiles = 22
        self.arena_left = max(0, (level.levelLength - arena_tiles) * 32)
        self.arena_right = (level.levelLength - 1) * 32

    @property
    def no_contact_damage(self):
        return self.brain.state in ("stunned", "dying", "dead")

    def on_hit(self, direction, damage=1, knockback=4, pop=-2):
        if self.brain.state in ("dying", "dead"):
            return
        self.brain.take_hit(min(damage, 3))  # projétil (99) não 1-shota o chefe
        self.hp = self.brain.hp
        self.hit_stun = 0  # chefe nao entra em stun-lock de knockback
        self.flash_timer = 8
        FX.hit_sparks(self.rect.centerx, self.rect.centery, direction)
        if self.brain.should_summon():
            self._summon_drones()

    def _summon_drones(self):
        cx = self.rect.centerx // 32
        self.levelObj.addDrone(max(1, cx - 4), 12)
        self.levelObj.addDrone(min(self.levelObj.levelLength - 2, cx + 4), 12)
        FX.shake(8, 3)

    def update(self, camera):
        if self.alive is None:
            return
        if self.flash_timer > 0:
            self.flash_timer -= 1

        player = camera.entity
        player_dx = player.rect.centerx - self.rect.centerx
        if not self.activated and abs(player_dx) < 600:
            self.activated = True
        if not self.activated:
            self._draw(camera)
            return

        # fisica basica
        self.applyGravity()
        self.rect.y += int(self.vel.y)
        self._clampToGround()

        hit_wall = False
        if self.brain.state == "charge":
            speed = self.brain.charge_speed()
            self.rect.x += self.brain.facing * speed
            if self.rect.left <= self.arena_left:
                self.rect.left = self.arena_left
                hit_wall = True
            elif self.rect.right >= self.arena_right:
                self.rect.right = self.arena_right
                hit_wall = True
        elif self.brain.state == "jump" and not self.onGround:
            self.rect.x += self.jump_dir * 4
            self.rect.left = max(self.rect.left, self.arena_left)
            self.rect.right = min(self.rect.right, self.arena_right)

        on_ground_for_brain = self.onGround and self.was_airborne
        if not self.onGround:
            self.was_airborne = True

        event = self.brain.tick(player_dx, hit_wall, on_ground_for_brain)

        if event == "wall_impact":
            FX.shake(10, 4)
            FX.dust(self.rect.centerx, self.rect.bottom, count=12)
            self.sound.play_sfx(self.sound.bump)
        elif event == "jump_start":
            self.vel.y = JUMP_VEL
            self.onGround = False
            self.was_airborne = False
            self.jump_dir = 1 if player_dx > 0 else -1
        elif event == "slam":
            self.was_airborne = False
            FX.shake(12, 5)
            FX.dust(self.rect.centerx, self.rect.bottom, count=16)
            self.sound.play_sfx(self.sound.brick_bump)
            self._spawn_shockwaves()
        elif event == "died":
            self.dashboard.points += 1000
            FX.explosion(self.rect.centerx, self.rect.centery, (255, 120, 60))
            FX.float_text("1000", self.rect.x, self.rect.y)
            self.levelObj.endPortalActive = True
            self.alive = None
            return

        if self.brain.state == "dying" and self.brain.timer % 10 == 0:
            ex = self.rect.x + random.randint(0, 64)
            ey = self.rect.y + random.randint(0, 64)
            FX.explosion(ex, ey, (255, 160, 60))
            FX.shake(6, 3)

        self._draw(camera)

    def _clampToGround(self):
        # chao da arena: topo do chao em y=416 (13*32); mantem simples e robusto
        floor_top = 13 * 32
        if self.rect.bottom >= floor_top:
            self.rect.bottom = floor_top
            self.vel.y = 0
            self.onGround = True
        else:
            self.onGround = False

    def _spawn_shockwaves(self):
        y = self.rect.bottom - 8
        for direction in (-1, 1):
            self.levelObj.enemy_projectiles.append(
                Projectile(self.rect.centerx, y, direction, self.screen,
                           owner="enemy", speed=SHOCKWAVE_SPEED,
                           color=(255, 160, 40), level=self.levelObj)
            )

    def _draw(self, camera):
        x = self.rect.x + camera.x
        y = self.rect.y
        s = self.brain.state
        # tremor de telegraph
        if s in ("telegraph_charge", "telegraph_jump"):
            x += random.randint(-2, 2)
        sprite_name = STATE_TO_SPRITE.get(s, "idle")
        images = self.enraged_images if self.brain.enraged else self.images
        image = images[sprite_name]
        if self.brain.facing == -1:
            image = pygame.transform.flip(image, True, False)
        flash = self.flash_timer > 0 and (self.flash_timer // 2) % 2 == 0
        if flash:
            image = image.copy()
            image.fill((80, 80, 80, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(image, (x, y))
