# Crazy World — Platformer in Python

A custom 2D sci-fi platformer built with Pygame: melee combo combat, hearts
and checkpoints, turret enemies and a final boss (Mega Bot). Built with a
scene-based architecture (menu, gameplay, pause, victory), persistent
save/settings, smooth camera follow, and a tuned audio system.

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
* Progress (best score, furthest phase reached) is saved automatically to
  `save/progress.json`; the menu offers CONTINUE once you've made progress.
* Music/SFX volume (0–10) is adjustable from OPTIONS and persisted to
  `settings.json`.

## Project layout

```
core/     engine-level singletons: config, logging, renderer, FX,
          scene manager, audio, save
ui/       scenes (menu, gameplay, pause, how-to-play, victory) + HUD
classes/  world/support code: Level, Camera, Collider, sprites, combat rules
entities/ player, enemies, boss, projectiles, pickups, platforms
traits/   composable player behaviors (move, jump, dash, melee, bounce)
levels/   phase data (JSON)
tools/    dev-only utilities (level viewer, sprite generator)
tests/    pytest suite (headless, no display required)
```

See `CLAUDE.md` for architecture details aimed at future contributors.

## Dependencies
* pygame
* pytest (tests only)
