import json
import pygame

from core.log import get_logger
from classes.Sprites import Sprites
from classes.Tile import Tile
from entities.Checkpoint import Checkpoint
from entities.Drone import Drone
from entities.HeavyBot import HeavyBot
from entities.WeaponPowerup import WeaponPowerup
from entities.PowerBox import PowerBox
from entities.MovingPlatform import MovingPlatform
from entities.Sentry import Sentry
from entities.Boss import Boss

log = get_logger(__name__)


class Level:
    def __init__(self, screen, sound, dashboard):
        self.sprites = Sprites()
        self.dashboard = dashboard
        self.sound = sound
        self.screen = screen
        self.level = None
        self.levelLength = 0
        self.entityList = []
        self.background = pygame.image.load("./img/background.png").convert()
        self.bgWidth = self.background.get_width()
        self.hasEndPortal = False
        self.endPortalRect = None
        self.enemy_projectiles = []
        self.endPortalActive = True
        self.boss = None
        self.portal_frames = [
            self.sprites.spriteCollection.get(f"end_portal_{i}").image
            for i in range(4)
        ]
        self.portal_anim_timer = 0
        self.portal_anim_frame = 0

    def loadLevel(self, levelname):
        log.info("Carregando fase %s", levelname)
        self.entityList = []
        self.hasEndPortal = False
        self.endPortalRect = None
        self.enemy_projectiles = []
        self.endPortalActive = True
        self.boss = None
        with open("./levels/{}.json".format(levelname)) as jsonData:
            data = json.load(jsonData)
            self.levelLength = data["length"]
            self.loadLayers(data)
            self.loadObjects(data)
            self.loadEntities(data)

    def loadEntities(self, data):
        # Dados de fase sao first-party: erro aqui e bug de conteudo e deve
        # falhar alto (um except silencioso ja escondeu bug critico de arena).
        entities = data.get("level", {}).get("entities", {})
        for x, y in entities.get("PowerBox", []):
            self.addPowerBox(x, y)
        for x, y in entities.get("Drone", []):
            self.addDrone(x, y)
        for x, y in entities.get("HeavyBot", []):
            self.addHeavyBot(x, y)
        for x, y in entities.get("Checkpoint", []):
            self.entityList.append(
                Checkpoint(self.screen, x, y, self, self.sound)
            )
        for x, y in entities.get("Sentry", []):
            self.entityList.append(
                Sentry(self.screen, x, y, self, self.sound, self.dashboard)
            )
        for x, y in entities.get("Boss", []):
            self.boss = Boss(self.screen, x, y, self,
                             self.sound, self.dashboard,
                             self.sprites.spriteCollection)
            self.entityList.append(self.boss)
            self.endPortalActive = False

        for platform in entities.get("MovingPlatform", []):
            self.entityList.append(MovingPlatform(
                platform[0], platform[1], self, self.screen,
                platform[2], platform[3], platform[4]
            ))

        for x, y in entities.get("EndPortal", []):
            # y e a linha onde os "pes" do portal encostam no chao (mesma
            # convencao de HeavyBot/Boss); como o portal tem 2 tiles de
            # altura, o rect precisa subir 1 tile a partir dai, senao a
            # metade de baixo fica desenhada dentro do chao.
            self.endPortalRect = pygame.Rect(x * 32, (y - 1) * 32, 64, 64)
            self.hasEndPortal = True

    def loadLayers(self, data):
        layers = []
        for x in range(*data["level"]["layers"]["sky"]["x"]):
            layers.append(
                (
                        [
                            Tile(self.sprites.spriteCollection.get("sky"), None)
                            for y in range(*data["level"]["layers"]["sky"]["y"])
                        ]
                        + [
                            Tile(
                                self.sprites.spriteCollection.get(
                                    "ground" if y == data["level"]["layers"]["ground"]["y"][0] else "ground_dirt"
                                ),
                                pygame.Rect(x * 32, (y - 1) * 32, 32, 32),
                            )
                            for y in range(*data["level"]["layers"]["ground"]["y"])
                        ]
                )
            )
        self.level = list(map(list, zip(*layers)))

    def loadObjects(self, data):
        for x, y in data["level"]["objects"]["bush"]:
            self.addBushSprite(x, y)
        for x, y in data["level"]["objects"]["cloud"]:
            self.addCloudSprite(x, y)
        for item in data["level"]["objects"]["pipe"]:
            if len(item) >= 3:
                self.addPipeSprite(item[0], item[1], item[2])
            elif len(item) == 2:
                self.addPipeSprite(item[0], item[1])
        for x, y in data["level"]["objects"]["sky"]:
            self.level[y][x] = Tile(self.sprites.spriteCollection.get("sky"), None)
        for x, y in data["level"]["objects"]["ground"]:
            self.level[y][x] = Tile(
                self.sprites.spriteCollection.get("ground"),
                pygame.Rect(x * 32, y * 32, 32, 32),
            )

    def updateEntities(self, cam):
        player = cam.entity
        for proj in self.enemy_projectiles[:]:
            proj.update(cam, [])
            if not proj.alive:
                self.enemy_projectiles.remove(proj)
        for entity in self.entityList[:]:
            entity.update(cam)
            if entity.alive is None:
                self.entityList.remove(entity)
        # A "colada" do jogador na plataforma acontece em check_platform_landing,
        # chamada por Yasmin.update() depois do seu proprio moveYasmin(). Se
        # fosse feita aqui (antes de yasmin.update() no loop do jogo), o
        # Collider.checkY() do jogador zeraria onGround logo em seguida e o
        # pulo nunca veria onGround=True enquanto andando de plataforma.

    def check_platform_landing(self, player):
        for entity in self.entityList:
            if not (isinstance(entity, MovingPlatform) and entity.alive):
                continue
            platform = entity
            # Nao usar colliderect: apos "colar" o jogador no topo da
            # plataforma (contato exato, profundidade zero), pygame trata
            # retangulos so se tocando como NAO colidindo, entao no frame
            # seguinte a checagem falharia e o jogador cairia. Por isso a
            # deteccao de "em cima" usa sobreposicao horizontal + folga
            # vertical tolerante em vez de colliderect.
            horiz_overlap = (
                player.rect.right > platform.rect.left
                and player.rect.left < platform.rect.right
            )
            vertical_gap = player.rect.bottom - platform.rect.top
            if horiz_overlap and player.vel.y >= 0 and -4 <= vertical_gap <= 10:
                player.rect.bottom = platform.rect.top
                player.vel.y = 0
                player.onGround = True
                # Collider.checkY() reseta inAir/jumpCount ao pousar num
                # tile solido (via jumpTrait.reset()/bounceTrait.reset()),
                # mas plataformas nao passam por ali - sem isso, inAir
                # ficava travado em True e a animacao mostrava a pose de
                # pulo o tempo todo em cima da plataforma.
                if player.traits is not None:
                    if "jumpTrait" in player.traits:
                        player.traits["jumpTrait"].reset()
                    if "bounceTrait" in player.traits:
                        player.traits["bounceTrait"].reset()
                # Usa o delta real que o rect da plataforma andou neste
                # frame (nao int(platform.vel)): o rect arredonda a
                # posicao float a cada frame, entao truncar vel de novo
                # aqui dessincroniza o jogador da plataforma aos poucos
                # (ele "escorrega" por ficar sempre um pouco atras).
                player.rect.x += platform.delta_x
                player.rect.y += platform.delta_y
                return

    def checkEndPortal(self, yasminRect):
        if not self.endPortalActive:
            return False
        if not self.hasEndPortal or self.endPortalRect is None:
            return False
        return yasminRect.colliderect(self.endPortalRect)

    def drawBackground(self, camera):
        offset_x = int(camera.pos.x * 32 * 0.3) % self.bgWidth
        self.screen.blit(self.background, (-offset_x, 0))
        self.screen.blit(self.background, (self.bgWidth - offset_x, 0))

    def drawLevel(self, camera):
        sky_sprite = self.sprites.spriteCollection.get("sky")
        self.drawBackground(camera)
        num_cols = len(self.level[0]) if self.level else 0
        x_start = max(0, 0 - int(camera.pos.x + 1))
        x_end = min(num_cols, 20 - int(camera.pos.x - 1))
        for y in range(0, 15):
            for x in range(x_start, x_end):
                if self.level[y][x].sprite is None:
                    continue
                if self.level[y][x].sprite is sky_sprite:
                    continue
                self.level[y][x].sprite.drawSprite(
                    x + camera.pos.x, y, self.screen
                )
        self.updateEntities(camera)
        if self.hasEndPortal and self.endPortalRect and self.endPortalActive:
            self.portal_anim_timer += 1
            if self.portal_anim_timer >= 8:
                self.portal_anim_timer = 0
                self.portal_anim_frame = (self.portal_anim_frame + 1) % len(self.portal_frames)
            self.screen.blit(
                self.portal_frames[self.portal_anim_frame],
                (self.endPortalRect.x + camera.x, self.endPortalRect.y),
            )

    def addCloudSprite(self, x, y):
        return

    def addPipeSprite(self, x, y, length=2):
        portal_top = 12
        try:
            for i in range(y, portal_top):
                self.level[i][x] = Tile(None, pygame.Rect(x * 32, i * 32, 32, 32))
                self.level[i][x + 1] = Tile(None, pygame.Rect((x + 1) * 32, i * 32, 32, 32))
            self.level[portal_top][x] = Tile(
                self.sprites.spriteCollection.get("portal_tl"),
                pygame.Rect(x * 32, portal_top * 32, 32, 32),
            )
            self.level[portal_top][x + 1] = Tile(
                self.sprites.spriteCollection.get("portal_tr"),
                pygame.Rect((x + 1) * 32, portal_top * 32, 32, 32),
            )
            self.level[portal_top + 1][x] = Tile(
                self.sprites.spriteCollection.get("portal_bl"),
                pygame.Rect(x * 32, (portal_top + 1) * 32, 32, 32),
            )
            self.level[portal_top + 1][x + 1] = Tile(
                self.sprites.spriteCollection.get("portal_br"),
                pygame.Rect((x + 1) * 32, (portal_top + 1) * 32, 32, 32),
            )
        except IndexError:
            return

    def addBushSprite(self, x, y):
        try:
            self.level[y][x] = Tile(self.sprites.spriteCollection.get("bush_1"), None)
            self.level[y][x + 1] = Tile(self.sprites.spriteCollection.get("bush_2"), None)
            self.level[y][x + 2] = Tile(self.sprites.spriteCollection.get("bush_3"), None)
        except IndexError:
            return

    def addDrone(self, x, y):
        self.entityList.append(
            Drone(self.screen, self.sprites.spriteCollection, x, y, self, self.sound, self.dashboard)
        )

    def addHeavyBot(self, x, y):
        self.entityList.append(
            HeavyBot(self.screen, self.sprites.spriteCollection, x, y, self, self.sound, self.dashboard)
        )

    def addWeaponPowerup(self, col, row):
        self.entityList.append(
            WeaponPowerup(self.screen, col, row, self, self.sound)
        )

    def addPowerBox(self, x, y):
        self.level[y][x] = Tile(None, pygame.Rect(x * 32, y * 32 - 1, 32, 32))
        self.entityList.append(
            PowerBox(
                self.screen,
                x,
                y,
                self.sound,
                self.dashboard,
                self,
                self.sprites.spriteCollection,
            )
        )
