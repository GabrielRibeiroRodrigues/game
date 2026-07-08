from core import config
from core import fx as FX
from classes.CombatRules import is_stomp, apply_damage
from classes.Animation import Animation
from classes.Camera import Camera
from classes.Collider import Collider
from classes.EntityCollider import EntityCollider
from classes.Input import Input
from classes.Sprites import Sprites
from entities.EntityBase import EntityBase
from entities.Projectile import Projectile
from traits.bounce import bounceTrait
from traits.go import GoTrait
from traits.jump import JumpTrait
from traits.melee import MeleeTrait

spriteCollection = Sprites().spriteCollection
smallAnimation = Animation(
    [
        spriteCollection["yasmin_run1"].image,
        spriteCollection["yasmin_run2"].image,
        spriteCollection["yasmin_run3"].image,
    ],
    spriteCollection["yasmin_idle"].image,
    spriteCollection["yasmin_jump"].image,
)


class Yasmin(EntityBase):
    def __init__(self, x, y, level, screen, dashboard, sound, gravity=config.PLAYER_GRAVITY):
        super(Yasmin, self).__init__(x, y, gravity)
        self.camera = Camera(self.rect, self)
        self.sound = sound
        self.input = Input(self)
        self.inAir = False
        self.inJump = False
        self.invincibilityFrames = 0
        self.traits = {
            "jumpTrait": JumpTrait(self),
            "goTrait": GoTrait(smallAnimation, screen, self.camera, self),
            "bounceTrait": bounceTrait(self),
        }
        self.meleeTrait = MeleeTrait(self)
        self.attackImage = spriteCollection["yasmin_break"].image
        self.powerup_active = False
        self.powerup_timer = 0
        self.powerup_duration = config.POWERUP_DURATION_FRAMES
        self.projectiles = []
        self.levelObj = level
        self.collision = Collider(self, level)
        self.screen = screen
        self.EntityCollider = EntityCollider(self)
        self.dashboard = dashboard
        self.dead = False
        self.was_on_ground = False
        self.max_hearts = config.PLAYER_MAX_HEARTS
        self.hearts = config.PLAYER_MAX_HEARTS
        self.checkpoint = None

    def update(self):
        if self.invincibilityFrames > 0:
            self.invincibilityFrames -= 1
        self.updateTraits()
        self.meleeTrait.update()
        self._checkMeleeHits()
        self._updateProjectiles()
        if self.powerup_active:
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                self.powerup_active = False
        self.moveYasmin()
        self.levelObj.check_platform_landing(self)
        self.camera.move()
        self.applyGravity()
        self.checkEntityCollision()
        self._checkEnemyProjectiles()
        self.input.update()
        if self.onGround and not self.was_on_ground:
            FX.dust(self.rect.centerx, self.rect.bottom)
        self.was_on_ground = self.onGround

    def moveYasmin(self):
        self.rect.y += self.vel.y
        self.collision.checkY()
        self.rect.x += self.vel.x
        self.collision.checkX()

    def _checkMeleeHits(self):
        hitbox = self.meleeTrait.get_hitbox()
        if hitbox is None:
            return
        heading = self.traits["goTrait"].heading
        for ent in self.levelObj.entityList:
            if ent.alive and ent.alive is not None and ent.type == "Mob":
                if ent in self.meleeTrait.hit_entities:
                    continue
                if hitbox.colliderect(ent.rect):
                    self.meleeTrait.hit_entities.add(ent)
                    ent.on_hit(
                        heading,
                        damage=self.meleeTrait.current_damage(),
                        knockback=self.meleeTrait.current_knockback(),
                        pop=self.meleeTrait.current_pop(),
                    )
                    self.sound.play_sfx(self.sound.kick)
                    FX.hit_sparks(hitbox.centerx, hitbox.centery, heading)
                    if self.meleeTrait.combo_stage == 3:
                        FX.hitstop(5)
                        FX.shake(6, 3)
                    else:
                        FX.hitstop(3)
                        FX.shake(4, 2)
        for proj in self.levelObj.enemy_projectiles:
            if proj.alive and hitbox.colliderect(proj.rect):
                proj.alive = False
                FX.hit_sparks(proj.rect.centerx, proj.rect.centery, heading)
                self.sound.play_sfx(self.sound.kick)

    def _updateProjectiles(self):
        for proj in self.projectiles[:]:
            proj.update(self.camera, self.levelObj.entityList)
            if not proj.alive:
                self.projectiles.remove(proj)

    def checkEntityCollision(self):
        for ent in self.levelObj.entityList[:]:
            collisionState = self.EntityCollider.check(ent)
            if collisionState.isColliding:
                if ent.type == "Item":
                    self._onCollisionWithItem(ent)
                elif ent.type == "Block":
                    self._onCollisionWithBlock(ent)
                elif ent.type == "Mob":
                    self._onCollisionWithMob(ent, collisionState)
                elif ent.type == "Checkpoint":
                    ent.activate()
                    self.checkpoint = ent.tile_pos

    def _checkEnemyProjectiles(self):
        for proj in self.levelObj.enemy_projectiles:
            if proj.alive and proj.rect.colliderect(self.rect):
                proj.alive = False
                self.take_damage(proj.rect.centerx)

    def _onCollisionWithItem(self, item):
        if item in self.levelObj.entityList:
            self.levelObj.entityList.remove(item)
        self.activatePowerup()
        self.sound.play_sfx(self.sound.powerup)

    def _onCollisionWithBlock(self, block):
        if not block.triggered:
            self.sound.play_sfx(self.sound.bump)
        block.triggered = True

    def _onCollisionWithMob(self, mob, collisionState):
        if not (mob.alive and mob.alive is not None):
            return
        if getattr(mob, "no_contact_damage", False):
            return
        if is_stomp(self.vel.y, self.rect.bottom, mob.rect):
            self.bounce()
            self.sound.play_sfx(self.sound.stomp)
            if getattr(mob, "is_boss", False):
                return
            if mob.hit_stun == 0:
                heading = 1 if mob.rect.centerx >= self.rect.centerx else -1
                mob.on_hit(heading, damage=1, knockback=2, pop=0)
                FX.hit_sparks(mob.rect.centerx, mob.rect.top, heading)
                FX.hitstop(3)
            return
        if mob.hit_stun == 0:
            self.take_damage(mob.rect.centerx)

    def take_damage(self, from_x):
        self.hearts, self.invincibilityFrames, applied = apply_damage(
            self.hearts, self.invincibilityFrames
        )
        if not applied:
            return
        self.sound.play_sfx(self.sound.bump)
        direction = 1 if self.rect.centerx >= from_x else -1
        self.vel.x = 4 * direction
        self.vel.y = -5
        FX.shake(6, 3)
        FX.hitstop(4)
        if self.hearts <= 0:
            self.gameOver()

    def activatePowerup(self):
        self.powerup_active = True
        self.powerup_timer = self.powerup_duration

    def fireProjectile(self):
        if not self.powerup_active:
            return
        direction = self.traits["goTrait"].heading
        px = self.rect.centerx
        py = self.rect.centery - 4
        self.projectiles.append(
            Projectile(px, py, direction, self.screen, owner="player",
                       level=self.levelObj)
        )

    def bounce(self):
        self.traits["bounceTrait"].jump = True

    def gameOver(self):
        """Marca a morte; a sequencia visual e conduzida pela GameplayScene."""
        self.dead = True

    def getPos(self):
        return self.camera.x + self.rect.x, self.rect.y

    def setPos(self, x, y):
        self.rect.x = x
        self.rect.y = y
