# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the game
python main.py

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_boss_brain.py -v

# Install dependencies
pip install -r requirements.txt
```

## Architecture

**Crazy World** is a 2D sci-fi platformer built with Pygame, structured around a Scene Manager. The game has 3 phases (`Phase1`, `Phase2`, `Phase3`) loaded from JSON files in `levels/`. `main.py` is a thin bootstrap: it owns the single `pygame.event.get()` loop and clock, and delegates everything else to the active `Scene`.

### Package layout

| Package | Role |
|---|---|
| `core/` | Engine-level singletons: `config.py` (all tunable constants), `log.py` (logging, not prints), `screen.py` (2x renderer, `Screen.present()`), `fx.py` (particles/shake/hitstop/fade/banner), `scene.py` (`Scene` + `SceneManager`), `audio.py` (`AudioManager`), `save.py` (`SaveManager`) |
| `ui/` | Scenes: `MenuScene`, `GameplayScene`, `PauseScene`, `HowToPlayScene`, `VictoryScene`, plus `dashboard.py` (HUD) |
| `classes/` | World/support code: `Level`, `Camera`, `Collider`, `EntityCollider`, `Sprites`/`Sprite`/`Spritesheet`, `Tile`, `Animation`, `Maths`, `Font`, `CombatRules`, `Input` |
| `entities/` | `EntityBase`, `EnemyBase` (shared enemy lifecycle), `Yasmin` (player), `Drone`, `HeavyBot`, `Sentry`, `Boss`/`BossBrain`, `Checkpoint`, `PowerBox`, `WeaponPowerup`, `MovingPlatform`, `Projectile` |
| `traits/` | Composable player behaviors: `go`, `jump`, `dash`, `melee`, `bounce`, `leftrightwalk` |
| `tools/` | Dev-only utilities, not imported by the game: `level_viewer.py`, `generate_yasmin.py` |

### Scene Manager (`core/scene.py`)

`SceneManager` holds a stack of `Scene` objects. Only the top scene receives events (`handle_event`) and runs its frame (`run_frame`). `push`/`pop` are for overlays (pause on top of gameplay); `switch` clears the stack (menu → gameplay → victory → menu). `main.py`'s loop is:

```python
events = pygame.event.get()
if FX.hitstop_active():
    FX.tick_hitstop()   # freeze-frame; only QUIT still processed
else:
    manager.tick(events, screen)
Screen.present()
clock.tick(config.FPS)
```

Transitions (`manager.push/pop/switch`) called from inside `handle_event`/`run_frame` take effect on the next tick — safe to call at any point in a scene's own code.

Death is **not** a blocking loop: `Yasmin.gameOver()` just sets `self.dead = True`; `GameplayScene` drives the closing-circle animation as a non-blocking `"dying"` sub-state and respawns at the last checkpoint (or level start) when it finishes.

### Config and physics (`core/config.py`)

All cross-cutting constants (tile size, window size/scale, FPS, player gravity, hearts, powerup duration, file paths) live in `core/config.py` with type hints. Feature-local tunables (combo timing in `MeleeTrait`, boss state durations in `BossBrain`, camera smoothing in `Camera`) stay as class/module constants next to the code that uses them — centralizing those into `config.py` would just add indirection.

Physics uses a **fixed 60 Hz timestep** (velocities in px/frame) — a deliberate choice for platformers: deterministic, and all existing physics/combat tests depend on it. `config.FPS` is both the render cap and the simulation step.

### Entity system

All entities extend `EntityBase` (`entities/EntityBase.py`), which provides:
- `vel` (Vec2D), `rect` (pygame.Rect), `gravity`, `hp`/`max_hp`
- `on_hit(direction, damage, knockback, pop)` — applies hit-stun and knockback
- `alive`: `True` = alive, `False` = dead-but-animating, `None` = remove from list

Common enemies (`Drone`, `HeavyBot`, `Sentry`) extend `entities/EnemyBase.py`, which centralizes the previously-triplicated hit-stun/knockback-decay/death/flash/points-and-FX cycle. Subclasses only implement `_behave(camera)` (movement/AI while alive and not stunned) and `_draw(camera, flash)`, and set `POINTS`/`DEATH_COLOR`/offset class attributes. `Boss` does **not** extend `EnemyBase` — it has its own damage/stun rules (see below).

Entity types are identified by the string `self.type`:
- `"Mob"` — damageable by melee/stomp/projectiles
- `"Item"` — collectible (e.g. WeaponPowerup)
- `"Block"` — pushable/breakable tile-entities
- `"Checkpoint"` — respawn beacon

### Traits (player mechanics)

Traits in `traits/` are composable behaviors attached to Yasmin:
- `GoTrait` — horizontal movement, `heading` (1=right, -1=left)
- `JumpTrait` — jump + double-jump
- `DashTrait` — left-shift dash with iframe window
- `MeleeTrait` — 3-hit combo state machine; `combo_stage` 1–3; stage 3 is the finisher

`MeleeTrait` is **not** in `self.traits` dict (traits that run via `updateTraits()`); it is updated manually in `Yasmin.update()`.

### Camera (`classes/Camera.py`)

Smooth exponential-lerp follow (`SMOOTHING` per frame) toward a target `FOLLOW_OFFSET_TILES` tiles from the left edge, clamped to the level bounds. Call `camera.snap()` right after spawning/respawning the player so the view doesn't visibly pan from the old position — `move()` is for the normal per-frame follow.

### Audio (`core/audio.py`)

`AudioManager` replaces the old `classes/Sound.py`. Same consumer-facing surface (sound attributes, `music_channel`/`sfx_channel`, `play_sfx`, `allowSFX`) plus: `music_volume`/`sfx_volume` (0–10, persisted via `SaveManager`), `play_music()`/`stop_music()` with fade in/out, `set_music_volume()`/`set_sfx_volume()`.

### Save/settings (`core/save.py`)

`SaveManager` loads/merges `settings.json` (music/sfx on-off + volumes) and `save/progress.json` (furthest unlocked phase, best score) with defaults on missing/corrupt files, and writes atomically (temp file + `os.replace`) so a crash mid-save can't corrupt the file. `save/` is gitignored.

### Boss system

`entities/BossBrain.py` is a pure state machine (no pygame dependency) for the Mega Bot:
- States: `idle → telegraph_charge → charge → stunned → idle → telegraph_jump → jump → idle`
- Enrages below 50% HP (faster charge, shorter idle, summons drones)
- `tick(player_dx, hit_wall, on_ground)` returns an event string on transitions

`entities/Boss.py` wraps `BossBrain` with rendering and integrates with the Level's entity/projectile lists. The boss's charge always terminates via wall-clamp against `Level.levelLength` — the arena bounds are computed from `levelLength`, which **must** be set before `loadEntities()` runs in `Level.loadLevel` (a prior bug had this backwards, making Phase 3 unwinnable).

### Level JSON format

```json
{
  "length": <int>,
  "level": {
    "layers": { "sky": {"x": [start, end], "y": [...]}, "ground": {"y": [...]} },
    "objects": { "bush": [[x,y],...], "cloud": [], "pipe": [[x,y,len],...], "sky": [], "ground": [] },
    "entities": {
      "Drone": [[x,y],...], "HeavyBot": [...], "Sentry": [...],
      "PowerBox": [...], "Checkpoint": [...], "MovingPlatform": [[x,y,w,h,dir],...],
      "Boss": [[x,y]], "EndPortal": [[x,y]]
    }
  }
}
```

The end portal spawns **disabled** when a Boss is present; it activates when the boss dies.

### Testing approach

Tests in `tests/` avoid pygame display by importing only pure logic classes:
- `test_scene_manager.py` — `SceneManager` stack/event routing (no pygame display)
- `test_boss_brain.py` — BossBrain state machine (no pygame)
- `test_enemy_base.py` — shared enemy hit-stun/death cycle
- `test_combat_rules.py` — `is_stomp` / `apply_damage`
- `test_fx_logic.py` — FX particle/shake/hitstop logic
- `test_melee_combo.py` — MeleeTrait combo state machine
- `test_projectile.py` — Projectile movement/bounds
- `test_camera.py` — smooth-follow math and clamping
- `test_save_manager.py` — settings/progress persistence, atomic writes
- `test_audio_gain.py` — volume-to-gain conversion

When adding new gameplay logic, extract pure rules into a separate module (like `CombatRules.py`) so they can be tested without a display.
