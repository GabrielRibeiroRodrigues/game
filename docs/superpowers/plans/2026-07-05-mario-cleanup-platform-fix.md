# Mario Cleanup + Platform Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remover entidades e sprites mortos do Mario, substituir o visual do PowerBox por desenho procedural, e corrigir dois bugs no MovingPlatform (overshoot de amplitude e duplo deslocamento do jogador).

**Architecture:** Três frentes independentes executadas em ordem: (1) deleção pura de código morto, (2) substituição visual do PowerBox com `pygame.draw`, (3) dois fixes pontuais no MovingPlatform via método `_clamp` puro + ajuste de `vel` em vez de `rect`.

**Tech Stack:** Python 3, Pygame 2.6, pytest

---

## Mapa de arquivos

| Arquivo | Ação |
|---------|------|
| `entities/Bruno.py` | DELETE |
| `entities/Tiago.py` | DELETE |
| `entities/Mushroom.py` | DELETE |
| `entities/Coin.py` | DELETE |
| `entities/CoinBox.py` | DELETE |
| `entities/CoinBrick.py` | DELETE |
| `entities/RandomBox.py` | DELETE |
| `entities/Item.py` | DELETE |
| `sprites/Goomba.json` | DELETE |
| `sprites/RedMushroom.json` | DELETE |
| `sprites/Animations.json` | DELETE |
| `sprites/ItemAnimations.json` | DELETE |
| `sprites/Bruno.json` | RENAME → `sprites/Drone.json` |
| `sprites/Koopa.json` | RENAME → `sprites/HeavyBot.json` |
| `classes/Sprites.py` | MODIFY — atualizar lista de JSONs |
| `entities/PowerBox.py` | MODIFY — reescrever visual, remover spriteCollection |
| `classes/Level.py` | MODIFY — addPowerBox + fix updateEntities |
| `entities/MovingPlatform.py` | MODIFY — adicionar _clamp, corrigir update() |
| `tests/test_moving_platform.py` | CREATE |

---

## Task 1: Deletar entidades mortas

**Files:**
- Delete: `entities/Bruno.py`, `entities/Tiago.py`, `entities/Mushroom.py`, `entities/Coin.py`, `entities/CoinBox.py`, `entities/CoinBrick.py`, `entities/RandomBox.py`, `entities/Item.py`

- [ ] **Step 1: Deletar os 8 arquivos de entidade mortos**

```bash
cd C:\Users\gb\jogos
Remove-Item entities/Bruno.py, entities/Tiago.py, entities/Mushroom.py, entities/Coin.py, entities/CoinBox.py, entities/CoinBrick.py, entities/RandomBox.py, entities/Item.py
```

- [ ] **Step 2: Confirmar que nenhum arquivo ativo os importa**

```bash
grep -r "from entities.Bruno\|from entities.Tiago\|from entities.Mushroom\|from entities.Coin\|from entities.Item" --include="*.py" .
```

Esperado: nenhuma saída (os únicos imports eram entre os próprios arquivos deletados).

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove entidades mortas herdadas do Mario (goomba, koopa, moeda, cogumelo)"
```

---

## Task 2: Deletar e renomear sprite JSONs + atualizar Sprites.py

**Files:**
- Delete: `sprites/Goomba.json`, `sprites/RedMushroom.json`, `sprites/Animations.json`, `sprites/ItemAnimations.json`
- Rename: `sprites/Bruno.json` → `sprites/Drone.json`, `sprites/Koopa.json` → `sprites/HeavyBot.json`
- Modify: `classes/Sprites.py`

- [ ] **Step 1: Deletar JSONs de sprites mortos**

```bash
Remove-Item sprites/Goomba.json, sprites/RedMushroom.json, sprites/Animations.json, sprites/ItemAnimations.json
```

- [ ] **Step 2: Renomear Bruno.json → Drone.json e Koopa.json → HeavyBot.json**

```bash
Rename-Item sprites/Bruno.json sprites/Drone.json
Rename-Item sprites/Koopa.json sprites/HeavyBot.json
```

- [ ] **Step 3: Atualizar classes/Sprites.py**

Substituir o conteúdo de `__init__` para refletir os novos nomes e remover os JSONs deletados.

Conteúdo novo de `classes/Sprites.py` (somente o `__init__`):

```python
def __init__(self):
    self.spriteCollection = self.loadSprites(
        [
            "./sprites/Yasmin.json",
            "./sprites/Drone.json",
            "./sprites/HeavyBot.json",
            "./sprites/BackgroundSprites.json",
            "./sprites/Portal.json",
        ]
    )
```

- [ ] **Step 4: Verificar que o jogo ainda carrega as sprites**

```bash
python -c "from classes.Sprites import Sprites; s = Sprites(); print(list(s.spriteCollection.keys()))"
```

Esperado: lista que inclui `drone-1`, `drone-2`, `drone-flat`, `heavybot-1`, `heavybot-2`, `heavybot-damaged`, `heavybot-damaged-2`, `ground`, `sky`, `portal_tl`, etc. **Sem erros.**

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove JSONs de sprites Mario e renomeia Bruno/Koopa para Drone/HeavyBot"
```

---

## Task 3: Substituir visual do PowerBox por pygame.draw

**Files:**
- Modify: `entities/PowerBox.py` (linhas 1–42 — reescrita completa)
- Modify: `classes/Level.py:236–249` — remover `spriteCollection` do addPowerBox

- [ ] **Step 1: Reescrever entities/PowerBox.py**

```python
import pygame

from entities.EntityBase import EntityBase


class PowerBox(EntityBase):
    _FONT = None  # inicializado na primeira instancia (pygame ja esta ativo)

    def __init__(self, screen, x, y, sound, dashboard, level, gravity=0):
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
        self._pulse = 0

        if PowerBox._FONT is None:
            PowerBox._FONT = pygame.font.SysFont("arial", 20, bold=True)

    def update(self, cam):
        self._pulse = (self._pulse + 1) % 40

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
        if not self.triggered:
            border = (0, 191, 255) if self._pulse < 20 else (0, 95, 143)
            pygame.draw.rect(self.screen, (10, 26, 46), (dx, dy, 32, 32))
            pygame.draw.rect(self.screen, border, (dx, dy, 32, 32), 2)
            txt = self._FONT.render("?", True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=(dx + 16, dy + 16)))
        else:
            pygame.draw.rect(self.screen, (26, 26, 42), (dx, dy, 32, 32))
            pygame.draw.rect(self.screen, (51, 51, 51), (dx, dy, 32, 32), 2)
```

- [ ] **Step 2: Atualizar addPowerBox em classes/Level.py**

Localizar o método `addPowerBox` (linha ~236) e remover `self.sprites.spriteCollection` do construtor:

```python
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
        )
    )
```

- [ ] **Step 3: Verificar que a importação do PowerBox em Level.py está correta**

`Level.py` já importa `from entities.PowerBox import PowerBox`. Confirmar que não há import de `spriteCollection` sendo passado em outro lugar:

```bash
grep -n "PowerBox(" classes/Level.py
```

Esperado: uma linha com `PowerBox(self.screen, x, y, self.sound, self.dashboard, self,)`.

- [ ] **Step 4: Rodar o jogo e checar PowerBox visualmente**

```bash
python main.py
```

Iniciar a Fase 1, encontrar o PowerBox (tile (11,9)), verificar:
- Caixa azul escuro com borda ciano pulsando e `?` branco
- Após bater com pulo: caixa cinza sem texto, WeaponPowerup aparece acima

- [ ] **Step 5: Commit**

```bash
git add entities/PowerBox.py classes/Level.py
git commit -m "feat: PowerBox com visual procedural sci-fi, remove dependencia do spritesheet Mario"
```

---

## Task 4: Corrigir overshoot de amplitude no MovingPlatform (TDD)

**Files:**
- Create: `tests/test_moving_platform.py`
- Modify: `entities/MovingPlatform.py`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_moving_platform.py`:

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from entities.MovingPlatform import MovingPlatform


def test_clamp_sem_overshoot_direita():
    """Plataforma que vai ultrapassar o limite deve ser clamped e inverter vel."""
    pos, vel = MovingPlatform._clamp(95, start=0, vel=10, amplitude=100)
    assert pos == 100   # clamped no limite exato
    assert vel == -10   # velocidade invertida


def test_clamp_sem_overshoot_esquerda():
    pos, vel = MovingPlatform._clamp(-95, start=0, vel=-10, amplitude=100)
    assert pos == -100
    assert vel == 10


def test_clamp_movimento_normal():
    """Dentro do limite: sem clamp, vel inalterada."""
    pos, vel = MovingPlatform._clamp(50, start=0, vel=10, amplitude=100)
    assert pos == 60
    assert vel == 10


def test_clamp_no_limite_exato():
    """Exatamente no limite: inverte mas nao move alem."""
    pos, vel = MovingPlatform._clamp(90, start=0, vel=10, amplitude=100)
    assert pos == 100
    assert vel == -10
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python -m pytest tests/test_moving_platform.py -v
```

Esperado: `FAILED` com `AttributeError: type object 'MovingPlatform' has no attribute '_clamp'`.

- [ ] **Step 3: Implementar `_clamp` e corrigir `update()` em entities/MovingPlatform.py**

Substituir o método `update` e adicionar `_clamp` logo abaixo:

```python
def update(self, camera):
    if self.direction == "horizontal":
        self.rect.x, self.vel = self._clamp(
            self.rect.x, self.startX, self.vel, self.amplitude
        )
    else:
        self.rect.y, self.vel = self._clamp(
            self.rect.y, self.startY, self.vel, self.amplitude
        )
    self.collisionRect = self.rect.copy()
    self.draw(camera)

@staticmethod
def _clamp(pos, start, vel, amplitude):
    """Move pos por vel e garante que nao ultrapasse start±amplitude."""
    new_pos = pos + vel
    new_vel = vel
    if abs(new_pos - start) >= amplitude:
        new_vel = -vel
        new_pos = start + amplitude * (1 if new_pos > start else -1)
    return new_pos, new_vel
```

- [ ] **Step 4: Rodar testes e confirmar que passam**

```bash
python -m pytest tests/test_moving_platform.py -v
```

Esperado: 4 × `PASSED`.

- [ ] **Step 5: Rodar suite completa para confirmar sem regressão**

```bash
python -m pytest tests/ -v
```

Esperado: todos passam.

- [ ] **Step 6: Commit**

```bash
git add entities/MovingPlatform.py tests/test_moving_platform.py
git commit -m "fix: MovingPlatform._clamp impede overshoot de amplitude (plataforma nao entra em blocos)"
```

---

## Task 5: Corrigir duplo deslocamento do jogador em plataformas

**Files:**
- Modify: `classes/Level.py:122–144` — método `updateEntities`

- [ ] **Step 1: Localizar as linhas do bug em classes/Level.py**

```bash
grep -n "platform.vel\|platform.direction" classes/Level.py
```

Esperado: linhas ~137–143 com `player.rect.x += platform.vel` e `player.rect.y += platform.vel`.

- [ ] **Step 2: Aplicar o fix — substituir atribuição direta ao rect por adição à vel**

Dentro de `updateEntities`, na seção de colisão com plataforma, substituir:

```python
# ANTES
if platform.direction == "horizontal":
    player.rect.x += platform.vel
else:
    player.rect.y += platform.vel
```

por:

```python
# DEPOIS
if platform.direction == "horizontal":
    player.vel.x += platform.vel
else:
    player.vel.y += platform.vel
```

Isso garante que `moveYasmin()` aplica o deslocamento em uma única passagem junto com a própria vel do jogador, e que `checkX()` / `checkY()` ainda corrige colisões de tile normalmente.

- [ ] **Step 3: Rodar suite de testes para confirmar sem regressão**

```bash
python -m pytest tests/ -v
```

Esperado: todos passam.

- [ ] **Step 4: Verificação manual no jogo**

```bash
python main.py
```

Testar em Phase1 (plataforma horizontal em [33,11]):
- Ficar parado em cima da plataforma → jogador se move junto com ela, sem acelerar
- Caminhar sobre a plataforma em movimento → movimento relativo normal
- Plataforma vertical em Phase2 ([33,9]) → jogador sobe/desce sem afundar

- [ ] **Step 5: Commit**

```bash
git add classes/Level.py
git commit -m "fix: plataforma soma vel ao jogador em vez de mover rect diretamente (elimina duplo deslocamento)"
```
