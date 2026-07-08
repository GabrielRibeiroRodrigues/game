# Crazy World — Edição Profissional — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o Crazy World em um jogo com game feel profissional (FX, hit-stop, shake, transições) e gameplay profundo (HP + checkpoints, combo de melee, stomp, inimigo Sentry, chefe Mega Bot), conforme o spec `docs/superpowers/specs/2026-07-03-professional-edition-design.md`.

**Architecture:** Polish sobre a engine atual. Dois módulos novos com estado global (`classes/Screen.py` = Renderer/janela 2x, `classes/FX.py` = partículas/hitstop/shake/fade/banner), lógica de combate testável isolada em `classes/CombatRules.py`, máquina de estados do chefe pura em `entities/BossBrain.py`. Entidades novas: `Checkpoint`, `Sentry`, `Boss`. Nada da física/colisão/câmera existente muda.

**Tech Stack:** Python 3 + pygame (já instalado), pytest para testes de lógica pura (sem display).

**Convenções deste plano:**
- Rode todos os comandos a partir de `c:\Users\12265587630\jogos`.
- Testes: `python -m pytest tests/ -v` (pytest importa pygame mas nunca inicializa display; nenhum teste pode chamar `convert()`, `pygame.font` ou `pygame.display`).
- Verificação manual: `python main.py` — feche com ESC no menu.
- Commits frequentes, um por task no mínimo.

---

## Task 0: Setup de testes

**Files:**
- Create: `tests/__init__.py` (vazio)
- Create: `tests/conftest.py`
- Modify: `requirements.txt`

- [ ] **Step 0.1: Criar arquivos**

`tests/__init__.py`: arquivo vazio.

`tests/conftest.py`:
```python
import os

# Evita que qualquer import indireto de pygame tente abrir janela/audio
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
```

`requirements.txt` — adicionar linha:
```
pytest
```

- [ ] **Step 0.2: Instalar e verificar**

Run: `python -m pip install pytest` e depois `python -m pytest tests/ -v`
Expected: `no tests ran` (exit sem erro de coleta).

- [ ] **Step 0.3: Commit**

```bash
git add tests/ requirements.txt
git commit -m "chore: setup pytest"
```

---

## Task 1: Renderer 2x (`classes/Screen.py`)

Janela 1280×960, surface interna 640×480, `present()` central. Nenhuma classe de jogo muda como desenha — todas continuam recebendo a surface interna como `screen`.

**Files:**
- Create: `classes/Screen.py`
- Modify: `main.py`, `classes/Menu.py:180`, `classes/Pause.py:28`, `classes/GameOverScreen.py:28`, `classes/VictoryScreen.py:30`, `classes/HowToPlay.py:75`, `entities/Yasmin.py:169,172`

- [ ] **Step 1.1: Criar `classes/Screen.py`**

```python
import pygame

INTERNAL_SIZE = (640, 480)
SCALE = 2

_renderer = None


class Renderer:
    def __init__(self):
        self.window = pygame.display.set_mode(
            (INTERNAL_SIZE[0] * SCALE, INTERNAL_SIZE[1] * SCALE)
        )
        self.surface = pygame.Surface(INTERNAL_SIZE).convert()

    def present(self):
        # Import local para evitar ciclo (FX ainda nao existe na Task 1;
        # o try/except mantem o Renderer funcional sem o FX)
        try:
            from classes import FX
            FX.draw_screen(self.surface)
            offset = FX.get_shake_offset()
        except ImportError:
            offset = (0, 0)
        scaled = pygame.transform.scale(self.surface, self.window.get_size())
        self.window.fill((0, 0, 0))
        self.window.blit(scaled, (offset[0] * SCALE, offset[1] * SCALE))
        pygame.display.flip()


def init():
    global _renderer
    _renderer = Renderer()
    return _renderer


def get_surface():
    return _renderer.surface


def present():
    _renderer.present()
```

- [ ] **Step 1.2: Usar o Renderer no `main.py`**

Em `main.py`, substituir:
```python
windowSize = 640, 480
```
por:
```python
from classes import Screen
```
e dentro de `main()`, substituir:
```python
    screen = pygame.display.set_mode(windowSize)
```
por:
```python
    Screen.init()
    screen = Screen.get_surface()
```

No loop de `run_phase`, substituir `pygame.display.update()` por `Screen.present()` (adicionar `from classes import Screen` já cobre).

- [ ] **Step 1.3: Substituir os `display.update`/`flip` espalhados**

Em cada arquivo abaixo, adicionar `from classes import Screen` no topo e trocar:
- `classes/Menu.py` linha 180 (`pygame.display.update()` no fim de `checkInput`) → `Screen.present()`
- `classes/Pause.py` linha 28 (`pygame.display.update()` em `update`) → `Screen.present()`
- `classes/GameOverScreen.py` linha 28 (`pygame.display.flip()`) → `Screen.present()`
- `classes/VictoryScreen.py` linha 30 (`pygame.display.flip()`) → `Screen.present()`
- `classes/HowToPlay.py` linha 75 (`pygame.display.flip()`) → `Screen.present()`
- `entities/Yasmin.py` linhas 169 e 172 (`pygame.display.update()` dentro de `gameOver`) → `Screen.present()`

- [ ] **Step 1.4: Verificação manual**

Run: `python main.py`
Expected: janela 1280×960, jogo idêntico porém 2x maior. Menu navegável, JOGAR entra na fase, pause (ESC) funciona, morrer e voltar ao menu funcionam.

- [ ] **Step 1.5: Commit**

```bash
git add classes/Screen.py main.py classes/Menu.py classes/Pause.py classes/GameOverScreen.py classes/VictoryScreen.py classes/HowToPlay.py entities/Yasmin.py
git commit -m "feat: janela 2x com renderer central (classes/Screen.py)"
```

---

## Task 2: Módulo FX (`classes/FX.py`) — TDD

Estado global de partículas, texto flutuante, shake, hit-stop, fade e banner de fase. Toda a lógica de timers é testável sem display (desenho só acontece em `draw_world`/`draw_screen`).

**Files:**
- Create: `classes/FX.py`
- Test: `tests/test_fx_logic.py`

- [ ] **Step 2.1: Escrever os testes**

`tests/test_fx_logic.py`:
```python
from classes import FX


def setup_function(_):
    FX.reset()


def test_hitstop_accumulates_max_not_sum():
    FX.hitstop(3)
    FX.hitstop(5)
    assert FX._hitstop == 5  # max, nao soma
    FX.hitstop(2)
    assert FX._hitstop == 5


def test_hitstop_tick():
    FX.hitstop(2)
    assert FX.hitstop_active()
    FX.tick_hitstop()
    FX.tick_hitstop()
    assert not FX.hitstop_active()


def test_shake_offset_zero_when_inactive():
    assert FX.get_shake_offset() == (0, 0)


def test_shake_decays_via_update():
    FX.shake(3, 4)
    off = FX.get_shake_offset()
    assert -4 <= off[0] <= 4 and -4 <= off[1] <= 4
    FX.update()
    FX.update()
    FX.update()
    assert FX.get_shake_offset() == (0, 0)


def test_particles_expire():
    FX.explosion(100, 100, (255, 0, 0))
    assert len(FX._particles) > 0
    for _ in range(200):
        FX.update()
    assert len(FX._particles) == 0


def test_float_text_expires():
    FX.float_text("100", 50, 50)
    assert len(FX._texts) == 1
    for _ in range(60):
        FX.update()
    assert len(FX._texts) == 0


def test_fade_in_reaches_zero():
    FX.fade_in(10)
    assert FX._fade_alpha == 255
    for _ in range(10):
        FX.update()
    assert FX._fade_alpha == 0


def test_banner_expires():
    FX.phase_banner("FASE 1")
    assert FX._banner is not None
    for _ in range(FX.BANNER_TOTAL + 1):
        FX.update()
    assert FX._banner is None


def test_reset_clears_everything():
    FX.explosion(0, 0, (255, 0, 0))
    FX.float_text("x", 0, 0)
    FX.shake(10, 5)
    FX.hitstop(10)
    FX.phase_banner("X")
    FX.fade_in(30)
    FX.reset()
    assert FX._particles == [] and FX._texts == []
    assert FX.get_shake_offset() == (0, 0)
    assert not FX.hitstop_active()
    assert FX._banner is None and FX._fade_alpha == 0
```

- [ ] **Step 2.2: Rodar e ver falhar**

Run: `python -m pytest tests/test_fx_logic.py -v`
Expected: FAIL — `cannot import name 'FX'` / módulo não existe.

- [ ] **Step 2.3: Implementar `classes/FX.py`**

```python
"""Efeitos globais: particulas, texto flutuante, screen shake, hit-stop,
fade e banner de fase. Estado de modulo; update() uma vez por frame."""
import random

import pygame

BANNER_SLIDE = 20   # frames deslizando para entrar
BANNER_HOLD = 60    # frames parado no centro
BANNER_TOTAL = BANNER_SLIDE * 2 + BANNER_HOLD

_particles = []   # dicts: x,y,vx,vy,life,max_life,color,size,gravity
_texts = []       # dicts: text,x,y,life
_shake_frames = 0
_shake_mag = 0
_hitstop = 0
_fade_alpha = 0
_fade_step = 0
_banner = None    # dict: text, timer
_font_cache = {}


def reset():
    global _shake_frames, _shake_mag, _hitstop, _fade_alpha, _fade_step, _banner
    _particles.clear()
    _texts.clear()
    _shake_frames = 0
    _shake_mag = 0
    _hitstop = 0
    _fade_alpha = 0
    _fade_step = 0
    _banner = None


# ---------- particulas ----------

def _spawn(x, y, vx, vy, life, color, size, gravity=0.0):
    _particles.append({
        "x": x, "y": y, "vx": vx, "vy": vy,
        "life": life, "max_life": life,
        "color": color, "size": size, "gravity": gravity,
    })


def dust(x, y, count=6):
    for _ in range(count):
        _spawn(x + random.uniform(-8, 8), y,
               random.uniform(-1.0, 1.0), random.uniform(-1.5, -0.3),
               random.randint(12, 22), (160, 160, 170), random.randint(2, 4))


def hit_sparks(x, y, direction):
    for _ in range(8):
        _spawn(x, y,
               direction * random.uniform(0.5, 4.0), random.uniform(-3.0, 3.0),
               random.randint(8, 16),
               random.choice([(255, 240, 120), (255, 255, 255)]),
               random.randint(2, 3))


def explosion(x, y, color):
    for _ in range(14):
        _spawn(x, y,
               random.uniform(-4.0, 4.0), random.uniform(-6.0, -1.0),
               random.randint(20, 40), color, random.randint(2, 5),
               gravity=0.3)


def trail(x, y, color=(0, 200, 255)):
    _spawn(x, y, random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5),
           random.randint(6, 12), color, 2)


def float_text(text, x, y):
    _texts.append({"text": str(text), "x": x, "y": y, "life": 40})


# ---------- shake / hitstop ----------

def shake(frames, magnitude):
    global _shake_frames, _shake_mag
    _shake_frames = max(_shake_frames, frames)
    _shake_mag = max(_shake_mag, magnitude)


def get_shake_offset():
    if _shake_frames <= 0:
        return (0, 0)
    return (random.randint(-_shake_mag, _shake_mag),
            random.randint(-_shake_mag, _shake_mag))


def hitstop(frames):
    global _hitstop
    _hitstop = max(_hitstop, frames)


def hitstop_active():
    return _hitstop > 0


def tick_hitstop():
    global _hitstop
    if _hitstop > 0:
        _hitstop -= 1


# ---------- fade / banner ----------

def fade_in(frames):
    """Comeca preto e clareia ao longo de `frames` (chamar update() por frame)."""
    global _fade_alpha, _fade_step
    _fade_alpha = 255
    # teto da divisao: garante alpha==0 em ate `frames` updates
    _fade_step = -max(1, (255 + frames - 1) // frames)


def set_fade(alpha):
    """Fade estatico (usado em fade-out manual pelos loops de tela)."""
    global _fade_alpha, _fade_step
    _fade_alpha = max(0, min(255, int(alpha)))
    _fade_step = 0


def phase_banner(text):
    global _banner
    _banner = {"text": text, "timer": BANNER_TOTAL}


# ---------- update / draw ----------

def update():
    global _shake_frames, _shake_mag, _fade_alpha, _fade_step, _banner
    for p in _particles[:]:
        p["life"] -= 1
        if p["life"] <= 0:
            _particles.remove(p)
            continue
        p["vy"] += p["gravity"]
        p["x"] += p["vx"]
        p["y"] += p["vy"]
    for t in _texts[:]:
        t["life"] -= 1
        t["y"] -= 0.8
        if t["life"] <= 0:
            _texts.remove(t)
    if _shake_frames > 0:
        _shake_frames -= 1
        if _shake_frames == 0:
            _shake_mag = 0
    if _fade_step != 0:
        _fade_alpha += _fade_step
        if _fade_alpha <= 0:
            _fade_alpha = 0
            _fade_step = 0
        elif _fade_alpha >= 255:
            _fade_alpha = 255
            _fade_step = 0
    if _banner is not None:
        _banner["timer"] -= 1
        if _banner["timer"] <= 0:
            _banner = None


def _font(size):
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont("arial", size, bold=True)
    return _font_cache[size]


def draw_world(screen, camera):
    """Particulas e textos em coordenadas de mundo (desloca pela camera)."""
    for p in _particles:
        alpha_ratio = p["life"] / p["max_life"]
        size = max(1, int(p["size"] * alpha_ratio))
        pygame.draw.circle(screen, p["color"],
                           (int(p["x"] + camera.x), int(p["y"])), size)
    for t in _texts:
        surf = _font(14).render(t["text"], True, (255, 255, 255))
        screen.blit(surf, (int(t["x"] + camera.x), int(t["y"])))


def draw_screen(screen):
    """Overlays de tela inteira: banner de fase e fade. Chamado pelo Renderer."""
    if _banner is not None:
        w = screen.get_width()
        elapsed = BANNER_TOTAL - _banner["timer"]
        surf = _font(56).render(_banner["text"], True, (255, 255, 255))
        cx = (w - surf.get_width()) // 2
        if elapsed < BANNER_SLIDE:
            x = int(-surf.get_width() + (cx + surf.get_width()) * elapsed / BANNER_SLIDE)
        elif elapsed < BANNER_SLIDE + BANNER_HOLD:
            x = cx
        else:
            t = elapsed - BANNER_SLIDE - BANNER_HOLD
            x = int(cx + (w - cx) * t / BANNER_SLIDE)
        shadow = _font(56).render(_banner["text"], True, (0, 0, 0))
        screen.blit(shadow, (x + 3, 183))
        screen.blit(surf, (x, 180))
    if _fade_alpha > 0:
        overlay = pygame.Surface(screen.get_size())
        overlay.fill((0, 0, 0))
        overlay.set_alpha(_fade_alpha)
        screen.blit(overlay, (0, 0))
```

- [ ] **Step 2.4: Rodar testes**

Run: `python -m pytest tests/test_fx_logic.py -v`
Expected: 9 PASS.

- [ ] **Step 2.5: Commit**

```bash
git add classes/FX.py tests/test_fx_logic.py
git commit -m "feat: modulo FX (particulas, shake, hitstop, fade, banner) com testes"
```

---

## Task 3: Integrar FX no loop do jogo

Hit-stop no loop, partículas desenhadas sobre o mundo, poeira ao aterrissar/dash, banner e fade-in no início de fase.

**Files:**
- Modify: `main.py` (`run_phase`), `entities/Yasmin.py`, `traits/dash.py`

- [ ] **Step 3.1: `run_phase` com FX**

Em `main.py`, adicionar `from classes import FX` e reescrever o corpo do loop de `run_phase`:

```python
def run_phase(screen, sound, dashboard, phase_name, phase_display):
    level = Level(screen, sound, dashboard)
    level.loadLevel(phase_name)

    dashboard.state = "start"
    dashboard.time = 0
    dashboard.ticks = 0
    dashboard.levelName = phase_display

    yasmin = Yasmin(0, 0, level, screen, dashboard, sound)
    dashboard.yasmin = yasmin

    FX.reset()
    FX.phase_banner("FASE " + phase_display)
    FX.fade_in(30)

    clock = pygame.time.Clock()

    while True:
        pygame.display.set_caption(
            "Crazy World - Fase {} - {:d} FPS".format(phase_display, int(clock.get_fps()))
        )

        if FX.hitstop_active():
            FX.tick_hitstop()
            pygame.event.pump()
            Screen.present()
            clock.tick(60)
            continue

        if yasmin.pause:
            yasmin.pauseObj.update()
        else:
            level.drawLevel(yasmin.camera)
            yasmin.update()
            FX.update()
            FX.draw_world(screen, yasmin.camera)
            dashboard.update()

        Screen.present()
        clock.tick(60)

        if yasmin.restart_phase:
            return "restart"
        if yasmin.go_to_menu:
            return "menu"
        if level.checkEndPortal(yasmin.rect):
            return "next"
```

(Nota: `yasmin.update()` passa a vir antes de `dashboard.update()` para o HUD ficar por cima; `Screen.present()` substitui o `pygame.display.update()` do loop.)

- [ ] **Step 3.2: Poeira ao aterrissar (`entities/Yasmin.py`)**

Adicionar `from classes import FX` no topo. No `__init__`, adicionar:
```python
        self.was_on_ground = False
```
No fim de `update()` (depois de `self.input.checkForInput()`), adicionar:
```python
        if self.onGround and not self.was_on_ground:
            FX.dust(self.rect.centerx, self.rect.bottom)
        self.was_on_ground = self.onGround
```

- [ ] **Step 3.3: Poeira no dash (`traits/dash.py`)**

Adicionar `from classes import FX` no topo. Dentro do bloco que inicia o dash (logo após `self.entity.vel.x = self.dashSpeed * direction` no trecho do fresh press), adicionar:
```python
                FX.dust(self.entity.rect.centerx, self.entity.rect.bottom, count=10)
```

- [ ] **Step 3.4: Verificação manual**

Run: `python main.py`
Expected: banner "FASE 1" desliza ao começar; fade-in do preto; poeira ao aterrissar de pulos e ao dar dash. Testes continuam verdes: `python -m pytest tests/ -v`.

- [ ] **Step 3.5: Commit**

```bash
git add main.py entities/Yasmin.py traits/dash.py
git commit -m "feat: FX integrado ao loop (hitstop, banner, fade, poeira)"
```

---

## Task 4: `on_hit` com dano/knockback + flash branco + FX de morte

**Files:**
- Modify: `entities/EntityBase.py`, `entities/Drone.py`, `entities/HeavyBot.py`, `entities/Projectile.py`

- [ ] **Step 4.1: Novo `on_hit` em `entities/EntityBase.py`**

Substituir o método `on_hit` por:
```python
    def on_hit(self, direction, damage=1, knockback=4, pop=-2):
        """direction: 1=direita, -1=esquerda (knockback vai nessa direcao)."""
        self.hp -= damage
        self.hit_stun = 20
        self.knockback_vel = direction * knockback
        self.vel.y = pop
```

- [ ] **Step 4.2: Flash branco + FX de morte em `entities/Drone.py`**

Adicionar `from classes import FX` no topo. Em `update()`, substituir o bloco:
```python
            if self.hit_stun == 0 and self.hp <= 0:
                self.alive = False
                self.timer = 0
                self.textPos = Vec2D(self.rect.x + 3, self.rect.y)
                self.dashboard.points += 100
            if (self.hit_stun // 4) % 2 == 0:
                self._draw(camera)
            return
```
por:
```python
            if self.hit_stun == 0 and self.hp <= 0:
                self.alive = False
                self.timer = 0
                self.dashboard.points += 100
                FX.explosion(self.rect.centerx, self.rect.centery, (120, 220, 255))
                FX.float_text("100", self.rect.x + 3, self.rect.y)
                FX.shake(6, 3)
            self._draw(camera, flash=(self.hit_stun // 2) % 2 == 0)
            return
```
Substituir `_draw` por:
```python
    def _draw(self, camera, flash=False):
        image = self.animation.image
        if flash:
            image = image.copy()
            image.fill((180, 180, 180), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(image, (self.rect.x + camera.x, self.rect.y))
```
(As chamadas existentes `self._draw(camera)` fora do hit_stun continuam válidas pelo default `flash=False`.)

Em `_onDead`, remover as duas linhas do texto manual:
```python
            self.textPos.y -= 0.5
            self.dashboard.drawText("100", self.textPos.x + camera.x, self.textPos.y, 8)
```
(o corpo `drone-flat` continua sendo desenhado).

- [ ] **Step 4.3: Mesmo tratamento em `entities/HeavyBot.py`**

Adicionar `from classes import FX`. Mesma substituição do bloco de hit_stun, com pontos/cor próprios:
```python
            if self.hit_stun == 0 and self.hp <= 0:
                self.alive = False
                self.timer = 0
                self.dashboard.points += 200
                FX.explosion(self.rect.centerx, self.rect.centery - 16, (255, 160, 60))
                FX.float_text("200", self.rect.x + 3, self.rect.y - 32)
                FX.shake(6, 3)
            self._draw(camera, flash=(self.hit_stun // 2) % 2 == 0)
            return
```
Substituir `_draw` por:
```python
    def _draw(self, camera, flash=False):
        key = "heavybot-1" if self.hp >= 2 else "heavybot-damaged"
        frame = self.spriteCollection.get(key).image
        if self.leftrightTrait.direction == 1:
            frame = pygame.transform.flip(frame, True, False)
        if flash:
            frame = frame.copy()
            frame.fill((180, 180, 180), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(frame, (self.rect.x + camera.x, self.rect.y - 32))
```
Em `_onDead`, remover as duas linhas do texto manual ("200"), mantendo o corpo.

- [ ] **Step 4.4: Projétil da jogadora 1-shot explícito**

Em `entities/Projectile.py`, trocar `entity.on_hit(self.direction)` por:
```python
                    entity.on_hit(self.direction, damage=99, knockback=6)
```

- [ ] **Step 4.5: Verificação**

Run: `python -m pytest tests/ -v` → PASS.
Run: `python main.py` → bater em Drone/HeavyBot: flash branco durante o stun, explosão de fragmentos + "100"/"200" flutuante + shake na morte.

- [ ] **Step 4.6: Commit**

```bash
git add entities/EntityBase.py entities/Drone.py entities/HeavyBot.py entities/Projectile.py
git commit -m "feat: on_hit com dano/knockback, flash branco e FX de morte"
```

---

## Task 5: Combo de melee 3 golpes — TDD

**Files:**
- Rewrite: `traits/melee.py`
- Modify: `entities/Yasmin.py` (`_checkMeleeHits`)
- Test: `tests/test_melee_combo.py`

- [ ] **Step 5.1: Escrever os testes**

`tests/test_melee_combo.py`:
```python
import pygame

from traits.melee import MeleeTrait


class FakeGo:
    heading = 1


class FakeEntity:
    def __init__(self):
        self.rect = pygame.Rect(100, 100, 32, 32)
        self.traits = {"goTrait": FakeGo()}


def make():
    return MeleeTrait(FakeEntity())


def run_frames(m, n):
    for _ in range(n):
        m.update()


def test_first_attack_starts_stage_1():
    m = make()
    m.trigger()
    assert m.combo_stage == 1
    assert m.is_attacking


def test_chain_within_window_advances_stage():
    m = make()
    m.trigger()
    run_frames(m, MeleeTrait.ATTACK_DURATION)  # fim do golpe 1
    assert not m.is_attacking
    m.trigger()  # dentro da janela
    assert m.combo_stage == 2
    run_frames(m, MeleeTrait.ATTACK_DURATION)
    m.trigger()
    assert m.combo_stage == 3


def test_queued_input_during_swing_chains():
    m = make()
    m.trigger()
    run_frames(m, 3)
    m.trigger()  # buffer no meio do golpe
    run_frames(m, MeleeTrait.ATTACK_DURATION - 3)
    assert m.combo_stage == 2
    assert m.is_attacking


def test_missed_window_goes_to_cooldown():
    m = make()
    m.trigger()
    run_frames(m, MeleeTrait.ATTACK_DURATION + MeleeTrait.CHAIN_WINDOW)
    assert m.cooldown > 0
    m.trigger()  # ignorado durante cooldown
    assert not m.is_attacking


def test_stage3_enters_cooldown_and_resets():
    m = make()
    for _ in range(3):
        m.trigger()
        run_frames(m, MeleeTrait.ATTACK_DURATION)
    assert m.cooldown == MeleeTrait.COOLDOWN
    run_frames(m, MeleeTrait.COOLDOWN)
    assert m.combo_stage == 0
    m.trigger()
    assert m.combo_stage == 1


def test_damage_and_knockback_per_stage():
    m = make()
    m.combo_stage = 1
    assert m.current_damage() == 1 and m.current_knockback() == 4
    m.combo_stage = 3
    assert m.current_damage() == 2 and m.current_knockback() == 8


def test_hitbox_only_while_attacking_and_follows_heading():
    m = make()
    assert m.get_hitbox() is None
    m.trigger()
    hb = m.get_hitbox()
    assert hb is not None and hb.left == m.entity.rect.right
    m.entity.traits["goTrait"].heading = -1
    hb = m.get_hitbox()
    assert hb.right == m.entity.rect.left


def test_hit_entities_reset_each_swing():
    m = make()
    m.trigger()
    m.hit_entities.add("enemy_a")
    run_frames(m, MeleeTrait.ATTACK_DURATION)
    m.trigger()
    assert m.hit_entities == set()
```

- [ ] **Step 5.2: Rodar e ver falhar**

Run: `python -m pytest tests/test_melee_combo.py -v`
Expected: FAIL (`ATTACK_DURATION` não existe, comportamento antigo).

- [ ] **Step 5.3: Reescrever `traits/melee.py`**

```python
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
        self.hit_entities = set() # entidades ja atingidas pelo golpe atual

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
```

- [ ] **Step 5.4: Rodar testes**

Run: `python -m pytest tests/test_melee_combo.py -v`
Expected: 8 PASS.

- [ ] **Step 5.5: Aplicar dano por golpe em `entities/Yasmin.py`**

Substituir `_checkMeleeHits` por:
```python
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
```

- [ ] **Step 5.6: Verificação**

Run: `python -m pytest tests/ -v` → PASS.
Run: `python main.py` → cliques encadeados dão 3 golpes; cada acerto tem faísca + micro-congelamento + shake; 3º golpe derruba HeavyBot (2 de dano) com knockback maior; um golpe não acerta o mesmo inimigo duas vezes.

- [ ] **Step 5.7: Commit**

```bash
git add traits/melee.py entities/Yasmin.py tests/test_melee_combo.py
git commit -m "feat: combo de melee 3 golpes com buffer e dano por estagio"
```

---

## Task 6: Corações da jogadora + stomp + HUD — TDD

**Files:**
- Create: `classes/CombatRules.py`
- Modify: `entities/Yasmin.py`, `classes/Dashboard.py`
- Test: `tests/test_combat_rules.py`

- [ ] **Step 6.1: Escrever os testes**

`tests/test_combat_rules.py`:
```python
import pygame

from classes.CombatRules import is_stomp, apply_damage


def test_stomp_when_falling_and_above():
    mob = pygame.Rect(100, 100, 32, 32)
    # jogadora caindo, pes acima do centro do mob
    assert is_stomp(player_vel_y=4, player_bottom=108, mob_rect=mob)


def test_no_stomp_when_rising():
    mob = pygame.Rect(100, 100, 32, 32)
    assert not is_stomp(player_vel_y=-4, player_bottom=108, mob_rect=mob)


def test_no_stomp_when_side_hit():
    mob = pygame.Rect(100, 100, 32, 32)
    # pes abaixo do centro do mob = colisao lateral
    assert not is_stomp(player_vel_y=4, player_bottom=130, mob_rect=mob)


def test_apply_damage_decrements_and_grants_invuln():
    hearts, invuln, applied = apply_damage(hearts=3, invincibility_frames=0)
    assert (hearts, invuln, applied) == (2, 90, True)


def test_apply_damage_blocked_by_invuln():
    hearts, invuln, applied = apply_damage(hearts=3, invincibility_frames=30)
    assert (hearts, invuln, applied) == (3, 30, False)


def test_apply_damage_can_reach_zero():
    hearts, invuln, applied = apply_damage(hearts=1, invincibility_frames=0)
    assert hearts == 0 and applied
```

- [ ] **Step 6.2: Rodar e ver falhar**

Run: `python -m pytest tests/test_combat_rules.py -v`
Expected: FAIL — módulo não existe.

- [ ] **Step 6.3: Criar `classes/CombatRules.py`**

```python
"""Regras puras de combate da jogadora (testaveis sem pygame display)."""

INVULN_FRAMES = 90


def is_stomp(player_vel_y, player_bottom, mob_rect):
    """Stomp = jogadora caindo com os pes acima do centro vertical do mob."""
    return player_vel_y > 0 and player_bottom <= mob_rect.centery


def apply_damage(hearts, invincibility_frames):
    """Retorna (hearts, invincibility_frames, dano_aplicado)."""
    if invincibility_frames > 0:
        return hearts, invincibility_frames, False
    return hearts - 1, INVULN_FRAMES, True
```

- [ ] **Step 6.4: Rodar testes**

Run: `python -m pytest tests/test_combat_rules.py -v`
Expected: 6 PASS.

- [ ] **Step 6.5: Usar em `entities/Yasmin.py`**

Adicionar import:
```python
from classes.CombatRules import is_stomp, apply_damage
```
No `__init__`, adicionar:
```python
        self.max_hearts = 3
        self.hearts = 3
        self.checkpoint = None
```
Substituir `_onCollisionWithMob` por:
```python
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
```

- [ ] **Step 6.6: Corações no HUD (`classes/Dashboard.py`)**

Adicionar `from classes import FX` não é necessário aqui. Em `update()`, após o bloco da barra de arma, adicionar:
```python
        if self.yasmin and self.state != "menu":
            self.drawHearts()
```
E o método:
```python
    def drawHearts(self):
        y = 58
        for i in range(self.yasmin.max_hearts):
            x = 52 + i * 26
            color = (255, 60, 80) if i < self.yasmin.hearts else (70, 70, 80)
            pygame.draw.circle(self.screen, color, (x + 4, y + 4), 5)
            pygame.draw.circle(self.screen, color, (x + 12, y + 4), 5)
            pygame.draw.polygon(
                self.screen, color,
                [(x - 1, y + 6), (x + 17, y + 6), (x + 8, y + 17)],
            )
```

- [ ] **Step 6.7: Verificação**

Run: `python -m pytest tests/ -v` → PASS.
Run: `python main.py` → 3 corações no HUD; tocar inimigo: perde 1 coração, knockback, pisca ~1,5s (invencível); pisar em inimigo por cima: quica e causa 1 de dano (Drone morre, HeavyBot fica danificado); 3º toque: animação de morte.

- [ ] **Step 6.8: Commit**

```bash
git add classes/CombatRules.py entities/Yasmin.py classes/Dashboard.py tests/test_combat_rules.py
git commit -m "feat: 3 coracoes, stomp e HUD de vida"
```

---

## Task 7: Checkpoints + respawn

**Files:**
- Create: `entities/Checkpoint.py`
- Modify: `classes/Level.py`, `entities/Yasmin.py`, `main.py`, `levels/Phase1.json`, `levels/Phase2.json`, `levels/Phase3.json`

- [ ] **Step 7.1: Criar `entities/Checkpoint.py`**

```python
import math

import pygame

from classes import FX
from entities.EntityBase import EntityBase


class Checkpoint(EntityBase):
    def __init__(self, screen, x, y, level, sound):
        super().__init__(x, y - 1, 0)
        self.obeyGravity = False
        self.screen = screen
        self.sound = sound
        self.type = "Checkpoint"
        self.tile_pos = (x, y)
        self.activated = False
        self.pulse = 0

    def activate(self):
        if self.activated:
            return
        self.activated = True
        self.sound.play_sfx(self.sound.powerup_appear)
        FX.explosion(self.rect.centerx, self.rect.y, (80, 255, 140))

    def update(self, camera):
        self.pulse += 0.15
        x = self.rect.x + camera.x
        y = self.rect.y
        # poste
        pygame.draw.rect(self.screen, (90, 95, 110), (x + 14, y - 16, 4, 48))
        pygame.draw.rect(self.screen, (60, 65, 80), (x + 8, y + 28, 16, 4))
        # luz
        if self.activated:
            radius = 6 + int(2 * math.sin(self.pulse))
            color = (80, 255, 140)
        else:
            radius = 6
            color = (120, 120, 130)
        pygame.draw.circle(self.screen, color, (x + 16, y - 20), radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (x + 16, y - 20), 2)
```

- [ ] **Step 7.2: Carregar no `classes/Level.py`**

Adicionar import:
```python
from entities.Checkpoint import Checkpoint
```
Em `loadEntities`, após o loop de HeavyBot, adicionar:
```python
            for x, y in entities.get("Checkpoint", []):
                self.entityList.append(
                    Checkpoint(self.screen, x, y, self, self.sound)
                )
```
(dentro do mesmo `try`).

- [ ] **Step 7.3: Colisão em `entities/Yasmin.py`**

Em `checkEntityCollision`, adicionar mais um ramo:
```python
                elif ent.type == "Checkpoint":
                    ent.activate()
                    self.checkpoint = ent.tile_pos
```

- [ ] **Step 7.4: Respawn em `main.py`**

`run_phase` ganha parâmetro e retorno novos — assinatura e trechos alterados:
```python
def run_phase(screen, sound, dashboard, phase_name, phase_display, spawn_point=None):
```
Após criar `yasmin`, adicionar:
```python
    if spawn_point is not None:
        yasmin.setPos(spawn_point[0] * 32, (spawn_point[1] - 1) * 32)
        yasmin.checkpoint = spawn_point
        for ent in level.entityList:
            if ent.type == "Checkpoint" and ent.tile_pos == spawn_point:
                ent.activated = True
```
Todos os `return "restart"` / `"menu"` / `"next"` viram:
```python
        if yasmin.restart_phase:
            return "restart", yasmin.checkpoint
        if yasmin.go_to_menu:
            return "menu", None
        if level.checkEndPortal(yasmin.rect):
            return "next", None
```
No `main()`, o loop principal vira:
```python
    current_phase = 0
    checkpoint = None

    while True:
        result, checkpoint_reached = run_phase(
            screen, sound, dashboard,
            PHASES[current_phase],
            PHASE_NAMES[current_phase],
            spawn_point=checkpoint,
        )

        if result == "next":
            checkpoint = None
            current_phase += 1
            if current_phase >= len(PHASES):
                victory_screen.show()
                current_phase = 0
                _back_to_menu(screen, sound, dashboard, menu)

        elif result == "restart":
            checkpoint = checkpoint_reached

        elif result == "menu":
            checkpoint = None
            current_phase = 0
            _back_to_menu(screen, sound, dashboard, menu)
```
Remover a linha `game_over_screen.show()` e a criação `game_over_screen = GameOverScreen(screen)` e o import de `GameOverScreen` (a morte já tem a animação de círculo + fade-in do respawn; a tela "GAME OVER" burocrática sai). **Não** deletar o arquivo `classes/GameOverScreen.py` (fica sem uso; remoção fora de escopo).

Nota: `dashboard.points` **não** é zerado no restart (pontos persistem no respawn, como no spec); continua zerado em `_back_to_menu`. Em `run_phase`, `dashboard.time`/`ticks` são zerados a cada chamada — aceito (timer por tentativa).

- [ ] **Step 7.5: Checkpoints nos JSONs**

Em `levels/Phase1.json`, dentro de `"entities"`, adicionar:
```json
            "Checkpoint": [
                [30, 13]
            ],
```
Em `levels/Phase2.json`:
```json
            "Checkpoint": [
                [32, 13]
            ],
```
Em `levels/Phase3.json`:
```json
            "Checkpoint": [
                [45, 13]
            ],
```
(y=13 põe a base do beacon no chão: EntityBase usa `y - 1` ⇒ rect.y = 12*32 = 384, base em 416 = topo do chão. Escolher x em trecho de chão sólido — os valores acima estão em chão contínuo nos três níveis.)

- [ ] **Step 7.6: Verificação**

Run: `python -m pytest tests/ -v` → PASS.
Run: `python main.py` → beacon cinza no meio da Fase 1; ao tocar: luz verde pulsante + som + partículas. Morrer depois disso: respawn no beacon (não no início), corações cheios, pontos mantidos, sem tela GAME OVER. Morrer antes do beacon: respawn no início.

- [ ] **Step 7.7: Commit**

```bash
git add entities/Checkpoint.py classes/Level.py entities/Yasmin.py main.py levels/Phase1.json levels/Phase2.json levels/Phase3.json
git commit -m "feat: checkpoints com respawn sem tela de game over"
```

---

## Task 8: Projéteis com dono (player/enemy) — TDD

**Files:**
- Rewrite: `entities/Projectile.py`
- Modify: `classes/Level.py`, `entities/Yasmin.py`
- Test: `tests/test_projectile.py`

- [ ] **Step 8.1: Escrever os testes**

`tests/test_projectile.py`:
```python
import pygame

from entities.Projectile import Projectile


class FakeCam:
    x = 0
    y = 0


class FakeMob:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.alive = True
        self.type = "Mob"
        self.hits = []

    def on_hit(self, direction, damage=1, knockback=4, pop=-2):
        self.hits.append(damage)


def test_player_projectile_one_shots_mob():
    mob = FakeMob(120, 100)
    # x=110: apos 1 update (speed 7) o rect 117..129 sobrepoe o mob em 120
    p = Projectile(110, 108, 1, screen=None, owner="player")
    p.update(FakeCam(), [mob])
    assert not p.alive
    assert mob.hits == [99]


def test_enemy_projectile_ignores_mobs():
    mob = FakeMob(120, 100)
    p = Projectile(100, 108, 1, screen=None, owner="enemy", speed=3)
    for _ in range(20):
        p.update(FakeCam(), [mob])
    assert mob.hits == []
    assert p.alive


def test_projectile_expires():
    p = Projectile(0, 0, 1, screen=None)
    for _ in range(p.lifetime + 1):
        p.update(FakeCam(), [])
    assert not p.alive


def test_projectile_dies_on_solid_tile():
    class FakeTile:
        rect = pygame.Rect(160, 96, 32, 32)

    class FakeLevelObj:
        level = [[FakeTile() for _ in range(10)] for _ in range(10)]

    p = Projectile(140, 100, 1, screen=None, level=FakeLevelObj())
    for _ in range(5):
        p.update(FakeCam(), [])
    assert not p.alive
```

- [ ] **Step 8.2: Rodar e ver falhar**

Run: `python -m pytest tests/test_projectile.py -v`
Expected: FAIL (`owner` inesperado).

- [ ] **Step 8.3: Reescrever `entities/Projectile.py`**

```python
import pygame

from classes import FX


class Projectile:
    def __init__(self, x, y, direction, screen, owner="player",
                 speed=7, color=(255, 80, 0), level=None):
        self.rect = pygame.Rect(x, y, 12, 8)
        self.screen = screen
        self.direction = direction
        self.speed = speed
        self.color = color
        self.owner = owner
        self.level = level  # Level (para colisao com tiles); opcional
        self.alive = True
        self.type = "Projectile"
        self.lifetime = 90 if owner == "player" else 240

    def _hits_solid_tile(self):
        if self.level is None:
            return False
        col = self.rect.centerx // 32
        row = self.rect.centery // 32
        try:
            tile = self.level.level[row][col]
        except IndexError:
            return True
        return tile.rect is not None

    def update(self, camera, entityList):
        if not self.alive:
            return
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            return
        self.rect.x += self.direction * self.speed
        if self._hits_solid_tile():
            self.alive = False
            return
        if self.owner == "player":
            for entity in entityList:
                if entity.alive and entity.alive is not None and entity.type == "Mob":
                    if self.rect.colliderect(entity.rect):
                        entity.on_hit(self.direction, damage=99, knockback=6)
                        self.alive = False
                        return
            FX.trail(self.rect.centerx, self.rect.centery)
        if self.screen is not None:
            pygame.draw.ellipse(
                self.screen,
                self.color,
                (self.rect.x + camera.x, self.rect.y + camera.y,
                 self.rect.width, self.rect.height),
            )
```
(Atenção: `Projectile.level` recebe o **objeto Level**, cujo atributo `.level` é a grade de tiles — mesmo padrão do `Collider`.)

- [ ] **Step 8.4: Rodar testes**

Run: `python -m pytest tests/test_projectile.py -v`
Expected: 4 PASS.

- [ ] **Step 8.5: Lista de projéteis inimigos no `classes/Level.py`**

No `__init__`, adicionar:
```python
        self.enemy_projectiles = []
```
No começo de `loadLevel`, junto do reset de `entityList`:
```python
        self.enemy_projectiles = []
```
Em `updateEntities`, no início do método:
```python
        for proj in self.enemy_projectiles[:]:
            proj.update(cam, [])
            if not proj.alive:
                self.enemy_projectiles.remove(proj)
```

- [ ] **Step 8.6: Yasmin interage com projéteis inimigos**

Em `entities/Yasmin.py`:

`fireProjectile` passa o level:
```python
        self.projectiles.append(
            Projectile(px, py, direction, self.screen, owner="player",
                       level=self.levelObj)
        )
```
Em `update()`, após `self.checkEntityCollision()`, adicionar:
```python
        self._checkEnemyProjectiles()
```
E o método:
```python
    def _checkEnemyProjectiles(self):
        for proj in self.levelObj.enemy_projectiles:
            if proj.alive and proj.rect.colliderect(self.rect):
                proj.alive = False
                self.take_damage(proj.rect.centerx)
```
No fim de `_checkMeleeHits` (dentro do `if hitbox is None: return` já tratado — adicionar após o loop de Mobs):
```python
        for proj in self.levelObj.enemy_projectiles:
            if proj.alive and hitbox.colliderect(proj.rect):
                proj.alive = False
                FX.hit_sparks(proj.rect.centerx, proj.rect.centery, heading)
                self.sound.play_sfx(self.sound.kick)
```

- [ ] **Step 8.7: Verificação**

Run: `python -m pytest tests/ -v` → PASS.
Run: `python main.py` → pegar o powerup e atirar: projétil agora morre em paredes e deixa rastro de partículas.

- [ ] **Step 8.8: Commit**

```bash
git add entities/Projectile.py classes/Level.py entities/Yasmin.py tests/test_projectile.py
git commit -m "feat: projeteis com dono, colisao com tiles e defesa via melee"
```

---

## Task 9: Inimigo Sentry

**Files:**
- Create: `entities/Sentry.py`
- Modify: `classes/Level.py`, `levels/Phase2.json`, `levels/Phase3.json`

- [ ] **Step 9.1: Criar `entities/Sentry.py`**

```python
import pygame

from classes import FX
from classes.Collider import Collider
from entities.EntityBase import EntityBase
from entities.Projectile import Projectile


class Sentry(EntityBase):
    RANGE_X = 8 * 32
    RANGE_Y = 2 * 32
    CHARGE_FRAMES = 45
    COOLDOWN_FRAMES = 75

    def __init__(self, screen, x, y, level, sound, dashboard):
        super().__init__(x, y - 1, 1.25)
        self.screen = screen
        self.levelObj = level
        self.sound = sound
        self.dashboard = dashboard
        self.collision = Collider(self, level)
        self.type = "Mob"
        self.hp = 2
        self.max_hp = 2
        self.state = "idle"       # idle -> charging -> cooldown
        self.state_timer = 0
        self.facing = -1

    def update(self, camera):
        if self.alive is None:
            return
        if not self.alive:
            self.alive = None
            return

        self.applyGravity()
        self.rect.y += int(self.vel.y)
        self.collision.checkY()

        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.rect.x += int(self.knockback_vel)
            self.knockback_vel *= 0.8
            if self.hit_stun == 0 and self.hp <= 0:
                self.dashboard.points += 200
                FX.explosion(self.rect.centerx, self.rect.centery, (255, 90, 90))
                FX.float_text("200", self.rect.x + 3, self.rect.y)
                FX.shake(6, 3)
                self.alive = False
                return
            self._draw(camera, flash=(self.hit_stun // 2) % 2 == 0)
            return

        player = camera.entity
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        in_range = abs(dx) <= self.RANGE_X and abs(dy) <= self.RANGE_Y
        if dx != 0:
            self.facing = 1 if dx > 0 else -1

        if self.state == "idle":
            if in_range:
                self.state = "charging"
                self.state_timer = self.CHARGE_FRAMES
        elif self.state == "charging":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self._fire()
                self.state = "cooldown"
                self.state_timer = self.COOLDOWN_FRAMES
        elif self.state == "cooldown":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.state = "idle"

        self._draw(camera)

    def _fire(self):
        px = self.rect.centerx + self.facing * 18
        py = self.rect.centery - 4
        self.levelObj.enemy_projectiles.append(
            Projectile(px, py, self.facing, self.screen, owner="enemy",
                       speed=3, color=(255, 60, 60), level=self.levelObj)
        )
        self.sound.play_sfx(self.sound.kick)

    def _draw(self, camera, flash=False):
        x = self.rect.x + camera.x
        y = self.rect.y
        body = (200, 200, 210) if flash else (90, 100, 120)
        dome = (255, 255, 255) if flash else (140, 150, 170)
        # base
        pygame.draw.rect(self.screen, body, (x + 2, y + 18, 28, 14))
        # cupula
        pygame.draw.circle(self.screen, dome, (x + 16, y + 16), 12)
        # canhao
        cx = x + 16 + self.facing * 10
        pygame.draw.rect(
            self.screen, body,
            (min(cx, x + 16), y + 12, abs(cx - (x + 16)) + 6, 6),
        )
        # luz de telegraph: pisca vermelho enquanto carrega
        if self.state == "charging" and (self.state_timer // 4) % 2 == 0:
            pygame.draw.circle(self.screen, (255, 60, 60), (x + 16, y + 10), 4)
        else:
            pygame.draw.circle(self.screen, (60, 220, 120), (x + 16, y + 10), 3)
```

- [ ] **Step 9.2: Carregar no `classes/Level.py`**

Import:
```python
from entities.Sentry import Sentry
```
Em `loadEntities`, dentro do `try`, após Checkpoint:
```python
            for x, y in entities.get("Sentry", []):
                self.entityList.append(
                    Sentry(self.screen, x, y, self, self.sound, self.dashboard)
                )
```

- [ ] **Step 9.3: Sentries nos JSONs**

`levels/Phase2.json` — em `"entities"`, adicionar:
```json
            "Sentry": [
                [27, 13], [48, 13]
            ],
```
(x=27 fica na ilhota de chão perto das plataformas 20–24; x=48 cobre a chegada do trecho 43–47.)

`levels/Phase3.json` — adicionar:
```json
            "Sentry": [
                [26, 13], [55, 13]
            ],
```

- [ ] **Step 9.4: Verificação**

Run: `python -m pytest tests/ -v` → PASS.
Run: `python main.py` → na Fase 2: torretas visíveis; ao se aproximar, luz pisca vermelha por ~0,75s e ela atira projétil vermelho lento; dá para destruir o projétil com melee; a Sentry morre com 2 golpes (ou 1 stomp + 1 golpe) valendo 200 pontos.

- [ ] **Step 9.5: Commit**

```bash
git add entities/Sentry.py classes/Level.py levels/Phase2.json levels/Phase3.json
git commit -m "feat: inimigo Sentry com telegraph e projeteis"
```

---

## Task 10: BossBrain (máquina de estados pura) — TDD

**Files:**
- Create: `entities/BossBrain.py`
- Test: `tests/test_boss_brain.py`

- [ ] **Step 10.1: Escrever os testes**

`tests/test_boss_brain.py`:
```python
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
```

- [ ] **Step 10.2: Rodar e ver falhar**

Run: `python -m pytest tests/test_boss_brain.py -v`
Expected: FAIL — módulo não existe.

- [ ] **Step 10.3: Criar `entities/BossBrain.py`**

```python
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
```

- [ ] **Step 10.4: Rodar testes**

Run: `python -m pytest tests/test_boss_brain.py -v`
Expected: 8 PASS.

- [ ] **Step 10.5: Commit**

```bash
git add entities/BossBrain.py tests/test_boss_brain.py
git commit -m "feat: maquina de estados do chefe (BossBrain) com testes"
```

---

## Task 11: Boss no jogo + arena Phase3 + portal condicionado + barra de HP

**Files:**
- Create: `entities/Boss.py`
- Modify: `classes/Level.py`, `classes/Dashboard.py`, `entities/Yasmin.py` (nada — já trata `is_boss`/`no_contact_damage`), `levels/Phase3.json`

- [ ] **Step 11.1: Criar `entities/Boss.py`**

```python
import random

import pygame

from classes import FX
from classes.Collider import Collider
from entities.BossBrain import BossBrain
from entities.EntityBase import EntityBase
from entities.Projectile import Projectile

JUMP_VEL = -16
SHOCKWAVE_SPEED = 4


class Boss(EntityBase):
    def __init__(self, screen, x, y, level, sound, dashboard):
        super().__init__(x, y, 1.25)
        self.rect = pygame.Rect(x * 32, (y - 2) * 32, 64, 64)
        self.screen = screen
        self.levelObj = level
        self.sound = sound
        self.dashboard = dashboard
        self.collision = Collider(self, level)
        self.brain = BossBrain()
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

        if event == "charge_start":
            pass
        elif event == "wall_impact":
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
        flash = self.flash_timer > 0 and (self.flash_timer // 2) % 2 == 0
        body = (230, 230, 240) if flash else (70, 80, 100)
        armor = (255, 255, 255) if flash else (110, 120, 145)
        # tremor de telegraph
        if s in ("telegraph_charge", "telegraph_jump"):
            x += random.randint(-2, 2)
        # corpo
        pygame.draw.rect(self.screen, body, (x, y + 8, 64, 56))
        pygame.draw.rect(self.screen, armor, (x + 4, y, 56, 20))
        pygame.draw.rect(self.screen, armor, (x - 4, y + 24, 10, 28))
        pygame.draw.rect(self.screen, armor, (x + 58, y + 24, 10, 28))
        # olho
        eye_color = (255, 60, 60)
        if s == "stunned":
            eye_color = (255, 220, 80)
        elif s in ("telegraph_charge", "telegraph_jump"):
            eye_color = (255, 60, 60) if (self.brain.timer // 4) % 2 == 0 else (255, 200, 200)
        ex = x + 32 + self.brain.facing * 10
        pygame.draw.circle(self.screen, eye_color, (ex, y + 14), 7)
        pygame.draw.circle(self.screen, (0, 0, 0), (ex, y + 14), 3)
        # pernas
        pygame.draw.rect(self.screen, body, (x + 8, y + 56, 14, 8))
        pygame.draw.rect(self.screen, body, (x + 42, y + 56, 14, 8))
```

- [ ] **Step 11.2: Carregar no `classes/Level.py` + portal condicionado**

Import:
```python
from entities.Boss import Boss
```
No `__init__` do Level, adicionar:
```python
        self.endPortalActive = True
        self.boss = None
```
Em `loadLevel`, junto dos resets:
```python
        self.endPortalActive = True
        self.boss = None
```
Em `loadEntities`, dentro do `try`, após Sentry:
```python
            for x, y in entities.get("Boss", []):
                self.boss = Boss(self.screen, x, y, self,
                                 self.sound, self.dashboard)
                self.entityList.append(self.boss)
                self.endPortalActive = False
```
Em `checkEndPortal`, primeira linha:
```python
        if not self.endPortalActive:
            return False
```
Em `drawLevel`, trocar a condição do desenho do portal:
```python
            if self.hasEndPortal and self.endPortalRect and self.endPortalActive:
```

- [ ] **Step 11.3: Barra de HP do chefe no `classes/Dashboard.py`**

Em `update()`, adicionar ao final (antes do `self.ticks += 1`):
```python
        if self.yasmin is not None:
            boss = getattr(self.yasmin.levelObj, "boss", None)
            if boss is not None and boss.alive and boss.activated \
                    and boss.brain.state not in ("dying", "dead"):
                ratio = boss.brain.hp / boss.brain.max_hp
                self.drawText("MEGA BOT", 250, 55, 14)
                pygame.draw.rect(self.screen, (0, 0, 0), (168, 74, 304, 14))
                pygame.draw.rect(self.screen, (200, 40, 40),
                                 (170, 76, int(300 * ratio), 10))
                pygame.draw.rect(self.screen, (255, 255, 255),
                                 (170, 76, 300, 10), 1)
```

- [ ] **Step 11.4: Nova `levels/Phase3.json` (arena no final)**

Substituir o arquivo inteiro por:
```json
{
    "id": 3,
    "length": 100,
    "level": {
        "objects": {
            "bush": [[4, 12], [35, 12], [65, 12]],
            "cloud": [[10, 2], [25, 4], [45, 2], [65, 3], [85, 2]],
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
            "sky": {"x": [0, 100], "y": [0, 13]},
            "ground": {"x": [0, 100], "y": [14, 16]}
        },
        "entities": {
            "Drone": [
                [5, 12], [14, 12], [25, 12], [38, 12], [55, 12], [68, 12], [72, 12]
            ],
            "HeavyBot": [
                [20, 12], [35, 12], [50, 12], [62, 12]
            ],
            "Sentry": [
                [26, 13], [55, 13]
            ],
            "Checkpoint": [
                [75, 13]
            ],
            "PowerBox": [
                [13, 10], [43, 8], [58, 7], [76, 10]
            ],
            "MovingPlatform": [
                [11, 11, "horizontal", 2, 1.5],
                [22, 10, "horizontal", 2, 2.0],
                [32, 9, "vertical", 2, 1.5],
                [40, 8, "horizontal", 3, 2.5],
                [52, 7, "horizontal", 2, 2.0],
                [58, 6, "vertical", 2, 2.0]
            ],
            "Boss": [
                [90, 13]
            ],
            "EndPortal": [
                [94, 12]
            ]
        }
    }
}
```
(Checkpoint da Task 7 em [45,13] é substituído por [75,13] — antes da arena, com um PowerBox extra em [76,10] para dar a arma antes do chefe.)

- [ ] **Step 11.5: Verificação**

Run: `python -m pytest tests/ -v` → PASS.
Run: `python main.py` e ir até o fim da Fase 3 (para testar rápido, temporariamente pode-se trocar `PHASES` em `main.py` para começar em "Phase3" — **reverter antes do commit**):
- Portal invisível/inativo antes do chefe morrer.
- Barra "MEGA BOT" aparece ao se aproximar.
- Chefe alterna investida (com telegraph tremendo/olho piscando) e salto com shockwaves rasantes puláveis.
- Investida na parede → atordoado (olho amarelo) por ~0,75s, sem dano de contato.
- Com 6 HP: acelera e invoca 2 Drones (uma vez).
- Ao morrer: explosões + shake ~1,5s, +1000 pontos, portal verde aparece e completa a fase → tela de vitória.

- [ ] **Step 11.6: Commit**

```bash
git add entities/Boss.py classes/Level.py classes/Dashboard.py levels/Phase3.json
git commit -m "feat: chefe Mega Bot com arena, barra de HP e portal condicionado"
```

---

## Task 12: Polimento final, docs e verificação completa

**Files:**
- Modify: `classes/HowToPlay.py`, `README.md`, `main.py` (fade entre telas)

- [ ] **Step 12.1: Fade ao entrar no jogo pelo menu**

Em `main.py`, `_back_to_menu` e o pós-menu de `main()` já funcionam; adicionar apenas suavização: em `main()`, logo após `while not menu.start: menu.update()`, e também no mesmo ponto dentro de `_back_to_menu`, nada é necessário — o fade-in já acontece em `run_phase` via `FX.fade_in(30)`. Verificar que é o caso e seguir (nenhuma mudança se já estiver suave).

- [ ] **Step 12.2: Atualizar `classes/HowToPlay.py`**

Substituir as listas `controls` e `tips` por:
```python
        controls = [
            ("MOVER",        "SETA ESQUERDA / DIREITA"),
            ("PULAR",        "ESPACO ou SETA CIMA (2x no ar)"),
            ("DASH",         "SHIFT ESQUERDO"),
            ("ATACAR",       "CLIQUE ESQUERDO (3 cliques = combo)"),
            ("PAUSAR",       "ESC ou F5"),
        ]
        tips = [
            "Encadeie 3 golpes: o terceiro e mais forte.",
            "Pise nos inimigos para dana-los por cima.",
            "Toque no beacon para salvar seu progresso na fase.",
            "Destrua projeteis das torretas com seu golpe.",
            "Derrote o MEGA BOT na Fase 3 para abrir o portal.",
        ]
```

- [ ] **Step 12.3: Atualizar `README.md`**

Substituir o conteúdo por:
```markdown
# Crazy World — Platformer in Python

A custom 2D sci-fi platformer built with Pygame: melee combo combat, hearts
and checkpoints, turret enemies and a final boss (Mega Bot).

## Running

* $ pip install -r requirements.txt
* $ python main.py

## Tests

* $ python -m pytest tests/ -v

## Controls

* Left/Right: move
* Space / Up: jump (press again mid-air for double jump)
* Left Shift: dash
* Left mouse click: melee attack (chain 3 clicks for a combo) / fire when
  the weapon powerup is active
* ESC / F5: pause

## Gameplay

* You have 3 hearts; touching enemies costs 1 (falling in a pit is instant death).
* Touch the beacon mid-level to set your respawn checkpoint.
* Stomp enemies from above, or use the 3-hit melee combo (3rd hit is stronger).
* Sentry turrets telegraph before shooting — destroy their shots with melee.
* Defeat the Mega Bot at the end of Phase 3 to open the victory portal.

## Dependencies
* pygame
* scipy
* pytest (tests only)
```

- [ ] **Step 12.4: Verificação completa**

1. `python -m pytest tests/ -v` → todos PASS.
2. Playthrough completo: `python main.py`, jogar da Fase 1 até a tela de vitória, verificando cada critério de sucesso do spec:
   - Acertos de melee: faísca + hit-stop + shake + som, sempre.
   - Morrer após checkpoint → respawn no beacon com pontos mantidos.
   - Chefe legível e derrotável; portal só depois dele.
   - Menu → COMO JOGAR atualizado; pause funciona; voltar ao menu zera estado.
   - Fases 1–3 completáveis sem crash; FPS estável (~60) no título da janela.
3. Se algo falhar, corrigir antes do commit final.

- [ ] **Step 12.5: Commit final**

```bash
git add classes/HowToPlay.py README.md main.py
git commit -m "docs: instrucoes atualizadas e polimento final"
```

---

## Riscos e observações para o executor

- **Ordem das tasks importa**: 1 (Screen) → 2 (FX) → 3 (integração) antes de qualquer task de combate; 8 (projéteis) antes de 9 (Sentry) e 11 (Boss); 10 (BossBrain) antes de 11.
- `Yasmin.py` tem `spriteCollection = Sprites()` **no nível do módulo** — nunca importar `entities.Yasmin` em testes (exige display). Os testes só importam `classes.FX`, `classes.CombatRules`, `traits.melee`, `entities.Projectile`, `entities.BossBrain` — todos seguros.
- `classes/FX.py` não pode importar `classes/Screen.py` (ciclo: Screen importa FX em `present`). Manter FX sem imports de módulos do jogo.
- O hit-stop pausa TUDO (inclusive input); durações são curtas (3–5 frames) — não aumentar sem testar.
- Ao editar os JSONs de fase, validar com `python -c "import json; json.load(open('levels/Phase3.json'))"`.
