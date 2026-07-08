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
_fade_overlay = None  # surface reutilizada entre frames de fade


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
    frames = max(1, frames)
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
        global _fade_overlay
        if _fade_overlay is None or _fade_overlay.get_size() != screen.get_size():
            _fade_overlay = pygame.Surface(screen.get_size())
            _fade_overlay.fill((0, 0, 0))
        _fade_overlay.set_alpha(_fade_alpha)
        screen.blit(_fade_overlay, (0, 0))
