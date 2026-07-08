# Crazy World — Auditoria Técnica e Roadmap de Refatoração

**Data:** 2026-07-06
**Base:** branch `feature/edicao-profissional` (41 testes verdes)
**Objetivo:** elevar a arquitetura ao padrão de estúdio indie profissional: Scene Manager, módulos organizados, constantes centralizadas, logging, áudio com volume/fade, save de progresso, câmera suave — sem regredir o gameplay já entregue pela Edição Profissional.

---

## 1. Relatório de problemas

### CRÍTICO

| # | Problema | Evidência | Consequência |
|---|---|---|---|
| C1 | **Loops bloqueantes donos do event queue** — cada tela roda seu próprio `while` + `pygame.event.get()`: `Menu.checkInput`, `Pause.update`, `HowToPlay.show`, `VictoryScreen.show` e, pior, `Yasmin.gameOver` (animação de ~240 iterações chamando `input.checkForInput()` de DENTRO do update do player) | `entities/Yasmin.py:224-246`, `classes/Menu.py:128`, `classes/Pause.py:39`, `classes/HowToPlay.py:30`, `classes/VictoryScreen.py:14` | Input engolido entre telas; reentrância de estado (pause durante a morte); transições impossíveis de padronizar; nenhuma tela nova pode ser adicionada sem duplicar o padrão |
| C2 | **`except Exception: pass` engolindo erros** em `Level.loadEntities` (quase escondeu o bug da arena do chefe), broad excepts em `Collider.checkX/checkY` e `MovingPlatform._loadSprite`; nenhum logging no projeto | `classes/Level.py:49`, `classes/Collider.py:17,40`, `entities/MovingPlatform.py:29` | Bugs de dados/level silenciosamente ignorados; diagnóstico impossível em produção |

### ALTO

| # | Problema | Evidência |
|---|---|---|
| A1 | **God object `Yasmin`** (254 linhas, 8 responsabilidades: física, input, combate melee, projéteis, dano, morte, pause, câmera) | `entities/Yasmin.py` |
| A2 | **Bloco hit-stun/morte triplicado** em Drone, HeavyBot e Sentry (mesmo knockback decay, flash, timing) | `entities/Drone.py:42-56`, `entities/HeavyBot.py:42-56`, `entities/Sentry.py:40-53` |
| A3 | **Valores mágicos por toda parte**: `32` (tile) em ~40 lugares, `640/480`, velocidades, cores, HP, durações — sem módulo de configuração | todo o projeto |
| A4 | **Câmera sem suavização**: snap instantâneo com offset mágico de 10 tiles, sem interpolação | `classes/Camera.py` |
| A5 | **Áudio primitivo**: volumes 0.2 hardcoded, sem controle de volume, sem fade in/out, sem mute global | `classes/Sound.py:7-9` |
| A6 | **Sem persistência de progresso**: `settings.json` guarda apenas 2 booleans; pontuação/fase perdidos ao fechar | `classes/Menu.py:49-73` |
| A7 | **`classes/` é um junk drawer**: renderer, FX, UI, mundo, física e utilidades no mesmo pacote sem coesão | `classes/` (24 arquivos) |

### MÉDIO

| # | Problema | Evidência |
|---|---|---|
| M1 | **Código morto**: `classes/GameOverScreen.py` e `classes/LevelComplete.py` (sem chamadores), `compile.py` (py2exe, referencia arquivos inexistentes), `Yasmin.powerUpState/restart/killEntity`, import `EntityCollider` morto em Drone/HeavyBot | grep de usos |
| M2 | **`sys.exit()` espalhado em 6 arquivos** — cada tela decide sozinha encerrar o processo | grep `sys.exit` |
| M3 | **scipy (1.4.1, antiga) como dependência inteira só para o blur do pause** (`GaussianBlur`); emite DeprecationWarning de `scipy.ndimage.filters` | `classes/GaussianBlur.py:2`, `requirements.txt` |
| M4 | **Física frame-dependente** (`clock.tick(60)` com velocidades por frame). **Decisão deliberada: manter timestep fixo de 60 Hz** — é o padrão determinístico de platformers 2D (o comportamento de combate/física testado depende disso); converter tudo para delta time teria alto risco de regressão e nenhum ganho perceptível. Fica documentado e centralizado em `core/config.py` (`FPS`). |
| M5 | **`Input` mistura leitura com efeitos** (seta pause, chama fireProjectile) e dá `sys.exit` | `classes/Input.py` |

### BAIXO

| # | Problema |
|---|---|
| B1 | Sem type hints/docstrings nos módulos legados (aplicar progressivamente nos módulos tocados) |
| B2 | `FX.draw_screen` aloca uma Surface de tela inteira por frame durante fades |
| B3 | HUD com coordenadas mágicas em `Dashboard` |

---

## 2. Roadmap (execução por prioridade)

| Etapa | Conteúdo | Ataca |
|---|---|---|
| **1. Fundações `core/`** | `core/config.py` (todas as constantes, type hints), `core/log.py` (logging), mover `Screen`→`core/screen.py` e `FX`→`core/fx.py`, blur do pause via `pygame.transform.smoothscale` (remove scipy), deletar código morto (GameOverScreen, LevelComplete, GaussianBlur, compile.py), excepts estreitos com log | C2, A3, A7, M1, M3, B2 |
| **2. Scene Manager** | `core/scene.py` (Scene + SceneManager com stack e fade entre cenas), pacote `ui/`: MenuScene, HowToPlayScene, GameplayScene (absorve `run_phase`), PauseScene (overlay), VictoryScene, sequência de morte não-bloqueante; `main.py` vira bootstrap de ~40 linhas com UM event loop; `sys.exit` centralizado | C1, M2, M5 |
| **3. Entidades** | `entities/enemy_base.py` (hit-stun/morte/flash compartilhados; Drone/HeavyBot/Sentry herdam), Yasmin sem código morto e sem responsabilidades de tela | A1, A2, M1 |
| **4. Câmera, áudio e save** | `classes/Camera.py` com smooth-follow (lerp) e clamps; `core/audio.py` (AudioManager: volumes música/sfx 0-10, fade in/out, mute, persistidos); `core/save.py` (progresso: fase desbloqueada, melhor pontuação; gravação atômica); menu com CONTINUAR + controles de volume | A4, A5, A6 |
| **5. Perf, docs e verificação** | overlay de fade reutilizado no FX, README/CLAUDE.md atualizados, suite completa + playthrough headless das 3 fases | B1-B3 |

**Regras de execução:** todos os 41 testes existentes permanecem verdes em cada etapa; lógica nova testável ganha testes (câmera, save, audio, scene stack); um commit por etapa no mínimo; resumo técnico após cada etapa.

## 3. Estrutura final de módulos

```
core/          config.py, log.py, screen.py, fx.py, scene.py, audio.py, save.py
ui/            menu_scene.py, gameplay_scene.py, pause_scene.py,
               howtoplay_scene.py, victory_scene.py, dashboard.py (HUD)
classes/       mundo e suporte: Level, Camera, Collider, EntityCollider,
               Sprites/Sprite/Spritesheet, Tile, Animation, Maths, Font,
               CombatRules, Input
entities/      EntityBase, enemy_base, Yasmin, Drone, HeavyBot, Sentry,
               Boss, BossBrain, Checkpoint, PowerBox, WeaponPowerup,
               MovingPlatform, Projectile
traits/        go, jump, dash, melee, bounce, leftrightwalk
levels/ img/ sfx/ sprites/  assets e dados (inalterados)
tools/         level_viewer.py, generate_yasmin.py (utilitários dev)
tests/         suite pytest
```
