# Crazy World - Plano de Implementação Completo

## Visão Geral

Refatoração completa do jogo para tema sci-fi com:
- Personagem: Yasmin (sprites já existentes)
- Inimigos: Drone (1 HP) e HeavyBot (2 HP) com knockback
- Combate melee: clique esquerdo do mouse, na direção que Yasmin está virada
- Powerup de arma: projétil temporário (10 segundos), spawn de PowerBox
- Sem moedas, sem seleção de fases
- 3 fases com plataformas móveis e design sensato
- Morte reinicia a fase atual; vitória após Fase 3

---

## Tarefas

### TASK 01 — EntityBase: sistema de HP e knockback
**Arquivo:** `entities/EntityBase.py`

Adicionar ao `__init__`:
```python
self.hp = 1
self.max_hp = 1
self.hit_stun = 0        # frames de invulnerabilidade
self.knockback_vel = 0   # velocidade horizontal de knockback
```

Adicionar método `on_hit(direction)`:
```python
def on_hit(self, direction):
    """direction: 1=right, -1=left (knockback empurra para esse lado)"""
    self.hp -= 1
    self.hit_stun = 20
    self.knockback_vel = direction * 4
```

Não mexer em mais nada nesse arquivo.

---

### TASK 02 — Drone.py (substitui Bruno/Goomba)
**Arquivo:** `entities/Drone.py` (criar)

```python
from copy import copy
from entities.EntityBase import EntityBase
from traits.leftright import LeftRightTrait


class Drone(EntityBase):
    def __init__(self, screen, spriteCollection, x, y, level, sound, dashboard):
        super().__init__(x, y - 1, 1.25)
        self.screen = screen
        self.spriteCollection = spriteCollection
        self.animation = copy(self.spriteCollection.get("drone-1").animation)
        self.sound = sound
        self.dashboard = dashboard
        self.level = level
        self.type = "Mob"
        self.hp = 1
        self.max_hp = 1
        self.leftrightTrait = LeftRightTrait(self)

    def update(self, camera):
        if not self.alive:
            return

        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.rect.x += int(self.knockback_vel)
            self.knockback_vel *= 0.8
            if self.hp <= 0:
                self.alive = False
            self._draw(camera)
            return

        self.leftrightTrait.update()
        self.animation.update()
        self._draw(camera)

    def _draw(self, camera):
        frame = self.spriteCollection.get("drone-1").image
        if self.leftrightTrait.heading == -1:
            import pygame
            frame = pygame.transform.flip(frame, True, False)
        self.screen.blit(frame, (self.rect.x + camera.x, self.rect.y + camera.y))
```

**Sprite JSON:** Renomear keys no `sprites/Bruno.json`:
- `"goomba-1"` → `"drone-1"`
- `"goomba-2"` → `"drone-2"`
- `"goomba-flat"` → `"drone-flat"`

Manter o arquivo como `sprites/Bruno.json` por ora (Level.py carrega por chave, não por arquivo).

---

### TASK 03 — HeavyBot.py (substitui Tiago/Koopa)
**Arquivo:** `entities/HeavyBot.py` (criar)

```python
from copy import copy
from entities.EntityBase import EntityBase
from traits.leftright import LeftRightTrait
import pygame


class HeavyBot(EntityBase):
    def __init__(self, screen, spriteCollection, x, y, level, sound, dashboard):
        super().__init__(x, y - 1, 1.25)
        self.screen = screen
        self.spriteCollection = spriteCollection
        self.sound = sound
        self.dashboard = dashboard
        self.level = level
        self.type = "Mob"
        self.hp = 2
        self.max_hp = 2
        self.leftrightTrait = LeftRightTrait(self)

    def update(self, camera):
        if not self.alive:
            return

        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.rect.x += int(self.knockback_vel)
            self.knockback_vel *= 0.8
            if self.hp <= 0:
                self.alive = False
            self._draw(camera)
            return

        self.leftrightTrait.update()
        self._draw(camera)

    def _draw(self, camera):
        key = "heavybot-1" if self.hp == 2 else "heavybot-damaged"
        frame = self.spriteCollection.get(key).image
        if self.leftrightTrait.heading == -1:
            frame = pygame.transform.flip(frame, True, False)
        self.screen.blit(frame, (self.rect.x + camera.x, self.rect.y + camera.y))
```

**Sprite JSON:** Renomear keys no `sprites/Koopa.json`:
- `"koopa-1"` → `"heavybot-1"`
- `"koopa-2"` → `"heavybot-2"`
- `"koopa-hiding"` → `"heavybot-damaged"`
- `"koopa-hiding-with-legs"` → `"heavybot-damaged-2"`

---

### TASK 04 — MeleeTrait
**Arquivo:** `traits/melee.py` (criar)

```python
import pygame


class MeleeTrait:
    def __init__(self, entity):
        self.entity = entity
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_duration = 12  # frames que o hitbox fica ativo
        self.cooldown = 0
        self.cooldown_duration = 20

    def trigger(self):
        if self.cooldown > 0:
            return
        self.is_attacking = True
        self.attack_timer = self.attack_duration
        self.cooldown = self.cooldown_duration

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.is_attacking = False

    def get_hitbox(self):
        """Retorna pygame.Rect do hitbox de ataque, ou None se não está atacando."""
        if not self.is_attacking:
            return None
        r = self.entity.rect
        heading = self.entity.traits["goTrait"].heading
        if heading == 1:  # direita
            return pygame.Rect(r.right, r.top + 4, 28, 24)
        else:             # esquerda
            return pygame.Rect(r.left - 28, r.top + 4, 28, 24)
```

---

### TASK 05 — Projectile.py
**Arquivo:** `entities/Projectile.py` (criar)

```python
import pygame
from entities.EntityBase import EntityBase


class Projectile(EntityBase):
    def __init__(self, x, y, direction, screen):
        super().__init__(x // 32, y // 32, 0)
        self.rect = pygame.Rect(x, y, 12, 8)  # pixel coords diretos
        self.screen = screen
        self.direction = direction  # 1=right, -1=left
        self.speed = 7
        self.type = "Projectile"
        self.lifetime = 90  # frames (~1.5s a 60fps)

    def update(self, camera, entityList):
        if not self.alive:
            return
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            return
        self.rect.x += self.direction * self.speed
        # Checar colisão com inimigos
        for entity in entityList:
            if entity.alive and entity.type == "Mob":
                if self.rect.colliderect(entity.rect):
                    entity.on_hit(self.direction)
                    self.alive = False
                    return
        # Desenhar
        color = (255, 80, 0)
        pygame.draw.ellipse(self.screen, color,
                            (self.rect.x + camera.x, self.rect.y + camera.y,
                             self.rect.width, self.rect.height))
```

---

### TASK 06 — WeaponPowerup.py (substitui Mushroom)
**Arquivo:** `entities/WeaponPowerup.py` (criar)

```python
import pygame
from entities.EntityBase import EntityBase
from traits.leftright import LeftRightTrait


class WeaponPowerup(EntityBase):
    def __init__(self, screen, x, y, level, sound):
        super().__init__(x, y, 1.25)
        self.screen = screen
        self.level = level
        self.sound = sound
        self.type = "Item"
        self.leftrightTrait = LeftRightTrait(self)

    def update(self, camera):
        if not self.alive:
            return
        self.leftrightTrait.update()
        color = (0, 200, 255)
        pygame.draw.rect(self.screen, color,
                         (self.rect.x + camera.x, self.rect.y + camera.y,
                          self.rect.width, self.rect.height))
        # Borda
        pygame.draw.rect(self.screen, (255, 255, 255),
                         (self.rect.x + camera.x, self.rect.y + camera.y,
                          self.rect.width, self.rect.height), 2)
```

---

### TASK 07 — PowerBox.py (substitui CoinBox/RandomBox para powerup)
**Arquivo:** `entities/PowerBox.py` (criar)

```python
from copy import copy
from entities.EntityBase import EntityBase


class PowerBox(EntityBase):
    def __init__(self, screen, spriteCollection, x, y, sound, dashboard, level, gravity=0):
        super().__init__(x, y, gravity)
        self.screen = screen
        self.spriteCollection = spriteCollection
        self.type = "Block"
        self.triggered = False
        self.time = 0
        self.maxTime = 10
        self.sound = sound
        self.dashboard = dashboard
        self.level = level
        self.vel = 1
        self.animation = copy(self.spriteCollection.get("CoinBox").animation)

    def update(self, cam):
        if self.alive and not self.triggered:
            self.animation.update()
        else:
            self.animation.image = self.spriteCollection.get("empty").image
            if self.triggered:
                self.level.addWeaponPowerup(self.rect.y // 32 - 1, self.rect.x // 32)
                self.triggered = False  # evita spam
            if self.time < self.maxTime:
                self.time += 1
                self.rect.y -= self.vel
            else:
                if self.time < self.maxTime * 2:
                    self.time += 1
                    self.rect.y += self.vel
        self.screen.blit(
            self.spriteCollection.get("sky").image,
            (self.rect.x + cam.x, self.rect.y + 2),
        )
        self.screen.blit(self.animation.image, (self.rect.x + cam.x, self.rect.y - 1))
```

---

### TASK 08 — Yasmin.py: combate melee + powerup de projétil
**Arquivo:** `entities/Yasmin.py`

**Mudanças:**

1. Imports a adicionar no topo:
```python
from traits.melee import MeleeTrait
from entities.Projectile import Projectile
```

2. No `__init__`, após criar traits existentes, adicionar:
```python
self.meleeTrait = MeleeTrait(self)
self.powerup_active = False
self.powerup_timer = 0
self.powerup_duration = 600  # 10s a 60fps
self.projectiles = []
self.restart_phase = False
self.go_to_menu = False
```

3. No método `update()`, chamar `self.meleeTrait.update()` e atualizar projéteis:
```python
self.meleeTrait.update()
for p in self.projectiles[:]:
    p.update(camera, self.level.entityList)
    if not p.alive:
        self.projectiles.remove(p)
if self.powerup_active:
    self.powerup_timer -= 1
    if self.powerup_timer <= 0:
        self.powerup_active = False
```

4. Método `fireProjectile()`:
```python
def fireProjectile(self):
    if not self.powerup_active:
        return
    direction = self.traits["goTrait"].heading
    px = self.rect.centerx
    py = self.rect.centery - 4
    self.projectiles.append(Projectile(px, py, direction, self.screen))
```

5. Método `activatePowerup()`:
```python
def activatePowerup(self):
    self.powerup_active = True
    self.powerup_timer = self.powerup_duration
```

6. No método que detecta morte (quando `self.alive == False`), setar `self.restart_phase = True`.

7. Método `checkEntityCollision()` — quando colide com WeaponPowerup:
```python
# Dentro do loop de colisão, verificar type == "Item"
if entity.type == "Item":
    entity.alive = False
    self.activatePowerup()
```

8. Combate melee — verificar hitbox contra inimigos no `update()`:
```python
hitbox = self.meleeTrait.get_hitbox()
if hitbox:
    for entity in self.level.entityList:
        if entity.alive and entity.type == "Mob":
            if hitbox.colliderect(entity.rect):
                direction = self.traits["goTrait"].heading
                entity.on_hit(direction)
```

---

### TASK 09 — Input.py: clique esquerdo = ataque/projétil
**Arquivo:** `classes/Input.py`

Substituir o handler de mouse. No método que processa eventos:
```python
elif event.type == pygame.MOUSEBUTTONDOWN:
    if event.button == 1:  # esquerdo
        if self.yasmin.powerup_active:
            self.yasmin.fireProjectile()
        else:
            self.yasmin.meleeTrait.trigger()
```

Remover qualquer código de adicionar moedas ou debug de inimigos.

---

### TASK 10 — Level.py: novos métodos, remover moedas/antigos
**Arquivo:** `classes/Level.py`

**Remover:**
- `addCoin()`, `addCoinBrick()`, `addGoomba()`, `addKoopa()`, `addRedMushroom()`

**Renomear/criar:**
- `addDrone(row, col)` → cria `Drone(screen, sprites, col, row, level, sound, dashboard)`
- `addHeavyBot(row, col)` → cria `HeavyBot(screen, sprites, col, row, level, sound, dashboard)`
- `addWeaponPowerup(row, col)` → cria `WeaponPowerup(screen, col, row, level, sound)`
- `addPowerBox(col, row)` → cria `PowerBox(screen, sprites, col, row, sound, dashboard, level)`
- `addMovingPlatform(col, row, direction, amplitude, speed)` → já existe, manter

**Em `loadEntities()`**, mapear novas chaves JSON:
```python
"Drone": self.addDrone,
"HeavyBot": self.addHeavyBot,
"PowerBox": self.addPowerBox,
"MovingPlatform": self.addMovingPlatform,
"EndPortal": self.addEndPortal,
```

Remover: `"Goomba"`, `"Koopa"`, `"CoinBox"`, `"coinBrick"`, `"coin"`, `"RandomBox"`

**No início de `loadLevel()`**, limpar entityList:
```python
self.entityList = []
```

**Imports a adicionar:**
```python
from entities.Drone import Drone
from entities.HeavyBot import HeavyBot
from entities.WeaponPowerup import WeaponPowerup
from entities.PowerBox import PowerBox
```

---

### TASK 11 — Dashboard.py: remover moedas, adicionar barra de powerup
**Arquivo:** `classes/Dashboard.py`

1. Remover variável `self.coins` e o display de moedas.
2. Adicionar referência a Yasmin: `self.yasmin = None` (será setado em main.py).
3. No método `update()` ou `draw()`, onde renderiza o HUD, adicionar barra de powerup:
```python
if self.yasmin and self.yasmin.powerup_active:
    ratio = self.yasmin.powerup_timer / self.yasmin.powerup_duration
    bar_width = int(100 * ratio)
    pygame.draw.rect(self.screen, (0, 200, 255), (10, 50, bar_width, 8))
    pygame.draw.rect(self.screen, (255, 255, 255), (10, 50, 100, 8), 1)
```

---

### TASK 12 — Menu.py: remover seleção de fases
**Arquivo:** `classes/Menu.py`

No método `chooseLevel()` (ou equivalente), ao clicar em "JOGAR" retornar diretamente `1` (fase 1) sem mostrar menu de seleção. Remover `drawLevelChooser()` e qualquer lógica de múltiplos botões de fase.

```python
def chooseLevel(self):
    # Simplificado: sempre começa na fase 1
    return 1
```

---

### TASK 13 — VictoryScreen
**Arquivo:** `classes/VictoryScreen.py` (criar)

```python
import pygame
import sys


class VictoryScreen:
    def __init__(self, screen, dashboard):
        self.screen = screen
        self.dashboard = dashboard

    def show(self):
        clock = pygame.time.Clock()
        font_big = pygame.font.SysFont("monospace", 48, bold=True)
        font_small = pygame.font.SysFont("monospace", 24)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return "menu"
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            self.screen.fill((5, 10, 30))
            title = font_big.render("MISSÃO COMPLETA", True, (0, 255, 180))
            subtitle = font_small.render(f"Pontos: {self.dashboard.points}", True, (200, 200, 200))
            hint = font_small.render("ENTER para voltar ao menu", True, (120, 120, 120))
            w, h = self.screen.get_size()
            self.screen.blit(title, (w // 2 - title.get_width() // 2, h // 2 - 80))
            self.screen.blit(subtitle, (w // 2 - subtitle.get_width() // 2, h // 2))
            self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h // 2 + 60))
            pygame.display.flip()
            clock.tick(60)
```

---

### TASK 14 — GameOverScreen
**Arquivo:** `classes/GameOverScreen.py` (criar)

```python
import pygame
import sys


class GameOverScreen:
    def __init__(self, screen):
        self.screen = screen

    def show(self):
        clock = pygame.time.Clock()
        font_big = pygame.font.SysFont("monospace", 48, bold=True)
        font_small = pygame.font.SysFont("monospace", 24)
        timer = 180  # 3 segundos
        while timer > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    return "restart"
            timer -= 1
            self.screen.fill((10, 0, 0))
            title = font_big.render("GAME OVER", True, (255, 50, 50))
            hint = font_small.render("Reiniciando fase...", True, (150, 150, 150))
            w, h = self.screen.get_size()
            self.screen.blit(title, (w // 2 - title.get_width() // 2, h // 2 - 40))
            self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h // 2 + 30))
            pygame.display.flip()
            clock.tick(60)
        return "restart"
```

---

### TASK 15 — main.py: loop de fases, sem seleção de nível
**Arquivo:** `main.py`

Substituir lógica atual por:

```python
import pygame
import sys
from classes.Menu import Menu
from classes.Level import Level
from classes.Dashboard import Dashboard
from classes.Sound import Sound
from classes.Camera import Camera
from classes.Input import Input
from entities.Yasmin import Yasmin
from classes.VictoryScreen import VictoryScreen
from classes.GameOverScreen import GameOverScreen

PHASES = ["Level3-1", "Level3-2", "Level3-3"]  # arquivos JSON das 3 fases


def run_phase(screen, sound, phase_name):
    """Roda uma fase até vitória, morte ou menu. Retorna 'next', 'restart' ou 'menu'."""
    dashboard = Dashboard(screen)
    level = Level(screen, sound, dashboard)
    level.loadLevel(phase_name)
    camera = Camera(level)
    yasmin = Yasmin(screen, level, sound, dashboard)
    dashboard.yasmin = yasmin
    inputHandler = Input(yasmin, sound, dashboard)

    clock = pygame.time.Clock()
    while True:
        screen.fill((10, 15, 40))  # fundo sci-fi
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            inputHandler.handleEvent(event)

        level.update(camera)
        yasmin.update(camera)
        for proj in yasmin.projectiles:
            proj.update(camera, level.entityList)
        dashboard.update()
        camera.update(yasmin)
        pygame.display.flip()
        clock.tick(60)

        if yasmin.restart_phase:
            return "restart"
        if yasmin.go_to_menu:
            return "menu"
        # Verifica EndPortal
        for entity in level.entityList:
            if hasattr(entity, 'type') and entity.type == "EndPortal":
                if yasmin.rect.colliderect(entity.rect):
                    return "next"


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Crazy World")
    sound = Sound()
    menu = Menu(screen, sound)

    while True:
        choice = menu.chooseLevel()  # retorna sempre 1 (JOGAR) ou sai
        if choice is None:
            break

        current_phase = 0
        while current_phase < len(PHASES):
            result = run_phase(screen, sound, PHASES[current_phase])
            if result == "next":
                current_phase += 1
                if current_phase >= len(PHASES):
                    # Vitória!
                    dashboard = Dashboard(screen)
                    vs = VictoryScreen(screen, dashboard)
                    vs.show()
                    break
            elif result == "restart":
                game_over = GameOverScreen(screen)
                game_over.show()
                # continua no mesmo current_phase
            elif result == "menu":
                break


if __name__ == "__main__":
    main()
```

---

### TASK 16 — Fase 1 JSON: Phase1 (plataformas básicas)
**Arquivo:** `levels/Phase1.json` (criar)

```json
{
    "id": 1,
    "length": 60,
    "level": {
        "objects": {
            "bush": [[3, 12], [20, 12], [45, 12]],
            "cloud": [[5, 3], [18, 2], [35, 4], [52, 3]],
            "pipe": [],
            "sky": [
                [12, 13], [12, 14], [13, 13], [13, 14],
                [25, 13], [25, 14], [26, 13], [26, 14], [27, 13], [27, 14],
                [38, 13], [38, 14], [39, 13], [39, 14]
            ],
            "ground": [
                [10, 11], [11, 11],
                [22, 10], [23, 10], [24, 10]
            ]
        },
        "layers": {
            "sky": {"x": [0, 60], "y": [0, 13]},
            "ground": {"x": [0, 60], "y": [14, 16]}
        },
        "entities": {
            "Drone": [
                [8, 12], [15, 12], [30, 12], [42, 12]
            ],
            "HeavyBot": [
                [20, 12]
            ],
            "PowerBox": [
                [12, 9]
            ],
            "coin": [],
            "coinBrick": [],
            "MovingPlatform": [
                [33, 11, "horizontal", 2, 1.5]
            ],
            "EndPortal": [
                [57, 12]
            ]
        }
    }
}
```

---

### TASK 17 — Fase 2 JSON: Phase2 (mais plataformas móveis)
**Arquivo:** `levels/Phase2.json` (criar)

```json
{
    "id": 2,
    "length": 70,
    "level": {
        "objects": {
            "bush": [[5, 12], [28, 12], [55, 12]],
            "cloud": [[8, 2], [22, 4], [40, 3], [60, 2]],
            "pipe": [],
            "sky": [
                [10, 13], [10, 14], [11, 13], [11, 14], [12, 13], [12, 14],
                [20, 13], [20, 14], [21, 13], [21, 14], [22, 13], [22, 14],
                [23, 13], [23, 14], [24, 13], [24, 14],
                [35, 13], [35, 14], [36, 13], [36, 14], [37, 13], [37, 14],
                [38, 13], [38, 14], [39, 13], [39, 14], [40, 13], [40, 14],
                [50, 13], [50, 14], [51, 13], [51, 14]
            ],
            "ground": [
                [15, 11],
                [28, 10], [29, 10],
                [45, 9]
            ]
        },
        "layers": {
            "sky": {"x": [0, 70], "y": [0, 13]},
            "ground": {"x": [0, 70], "y": [14, 16]}
        },
        "entities": {
            "Drone": [
                [6, 12], [18, 12], [32, 12], [52, 12], [60, 12]
            ],
            "HeavyBot": [
                [25, 12], [44, 12]
            ],
            "PowerBox": [
                [16, 10], [46, 8]
            ],
            "coin": [],
            "coinBrick": [],
            "MovingPlatform": [
                [13, 11, "horizontal", 2, 1.5],
                [23, 10, "horizontal", 2, 2.0],
                [33, 9, "vertical", 2, 1.5],
                [43, 8, "horizontal", 3, 2.0]
            ],
            "EndPortal": [
                [67, 12]
            ]
        }
    }
}
```

---

### TASK 18 — Fase 3 JSON: Phase3 (desafio final)
**Arquivo:** `levels/Phase3.json` (criar)

```json
{
    "id": 3,
    "length": 80,
    "level": {
        "objects": {
            "bush": [[4, 12], [35, 12], [65, 12]],
            "cloud": [[10, 2], [25, 4], [45, 2], [65, 3]],
            "pipe": [],
            "sky": [
                [8, 13], [8, 14], [9, 13], [9, 14], [10, 13], [10, 14],
                [18, 13], [18, 14], [19, 13], [19, 14], [20, 13], [20, 14],
                [21, 13], [21, 14], [22, 13], [22, 14], [23, 13], [23, 14],
                [30, 13], [30, 14], [31, 13], [31, 14], [32, 13], [32, 14],
                [33, 13], [33, 14], [34, 13], [34, 14], [35, 13], [35, 14],
                [36, 13], [36, 14], [37, 13], [37, 14],
                [48, 13], [48, 14], [49, 13], [49, 14], [50, 13], [50, 14],
                [51, 13], [51, 14], [52, 13], [52, 14],
                [60, 13], [60, 14], [61, 13], [61, 14]
            ],
            "ground": [
                [12, 11],
                [27, 10], [28, 10],
                [42, 9], [43, 9],
                [57, 8]
            ]
        },
        "layers": {
            "sky": {"x": [0, 80], "y": [0, 13]},
            "ground": {"x": [0, 80], "y": [14, 16]}
        },
        "entities": {
            "Drone": [
                [5, 12], [14, 12], [25, 12], [38, 12], [55, 12], [68, 12], [72, 12]
            ],
            "HeavyBot": [
                [20, 12], [35, 12], [50, 12], [62, 12]
            ],
            "PowerBox": [
                [13, 10], [43, 8], [58, 7]
            ],
            "coin": [],
            "coinBrick": [],
            "MovingPlatform": [
                [11, 11, "horizontal", 2, 1.5],
                [22, 10, "horizontal", 2, 2.0],
                [32, 9, "vertical", 2, 1.5],
                [40, 8, "horizontal", 3, 2.5],
                [52, 7, "horizontal", 2, 2.0],
                [58, 6, "vertical", 2, 2.0]
            ],
            "EndPortal": [
                [77, 12]
            ]
        }
    }
}
```

---

### TASK 19 — Limpeza: remover arquivos legados
**Arquivos a deletar:**
- `entities/Bruno.py`
- `entities/Tiago.py`
- `entities/Mushroom.py`
- `entities/Item.py` (spawnCoin não é mais usado)
- `levels/Level1-1.json`
- `levels/Level1-2.json`

**Sprites JSON a atualizar (renomear keys):**
- `sprites/Bruno.json`: `goomba-*` → `drone-*`
- `sprites/Koopa.json`: `koopa-*` → `heavybot-*`

**Level.py**: Remover imports de `Bruno`, `Tiago`, `Mushroom`, `Item`, `CoinBox`, `RandomBox`.

---

## Ordem de Execução Recomendada

1. TASK 01 — EntityBase (base para tudo)
2. TASK 04 — MeleeTrait
3. TASK 05 — Projectile
4. TASK 06 — WeaponPowerup
5. TASK 02 — Drone
6. TASK 03 — HeavyBot
7. TASK 07 — PowerBox
8. TASK 19 — Renomear keys nos JSONs de sprite (antes de testar)
9. TASK 10 — Level.py
10. TASK 08 — Yasmin.py
11. TASK 09 — Input.py
12. TASK 11 — Dashboard.py
13. TASK 12 — Menu.py
14. TASK 13 — VictoryScreen
15. TASK 14 — GameOverScreen
16. TASK 15 — main.py
17. TASK 16-18 — JSONs das 3 fases
18. TASK 19 — Deletar legados

---

## Checklist de Teste

- [ ] Yasmin aparece e anda normalmente
- [ ] Clique esquerdo sem powerup → animação de soco, inimigo próximo toma dano
- [ ] Drone morre em 1 hit, bate em 1
- [ ] HeavyBot muda visual em 1 hit, morre em 2
- [ ] PowerBox hit-from-below → WeaponPowerup aparece
- [ ] Coletar WeaponPowerup → barra azul aparece no HUD
- [ ] Com powerup: clique esquerdo dispara projétil
- [ ] Projétil destrói Drone e HeavyBot em 1 hit
- [ ] Barra de powerup esgota em ~10s
- [ ] MovingPlatform carrega Yasmin corretamente
- [ ] Pit (tiles "sky") mata Yasmin → tela game over → reinicia fase
- [ ] EndPortal carrega próxima fase
- [ ] Fase 3 → EndPortal → tela de vitória
- [ ] Menu JOGAR → começa direto na Fase 1
