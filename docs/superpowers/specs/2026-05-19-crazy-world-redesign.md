# Crazy World — Redesign Completo (Option B)

**Data:** 2026-05-19  
**Status:** Aprovado pelo usuário

---

## Visão Geral

Refatoração completa do jogo para remover toda herança visual e mecânica do Super Mario. O universo é ficção científica (sprites e fundo já parcialmente alterados). O foco muda para combate corpo a corpo com sistema de HP e plataformas móveis com sequências de sincronização.

---

## O que é Removido

| Item | Motivo |
|---|---|
| `Level1-1.json`, `Level1-2.json` | Fases antigas descartadas |
| `entities/Coin.py` | Sistema de moedas removido |
| `entities/CoinBox.py` | Substituído por PowerBox |
| `entities/CoinBrick.py` | Removido |
| `dashboard.coins` | Tracking de moedas removido |
| Tela de seleção de nível | Sempre começa na Fase 1 |
| Cogumelo que cresce Yasmin (RedMushroom) | Substituído por arma temporária |
| Toda nomenclatura "goomba"/"koopa" interna | Renomeado para universo sci-fi |

---

## Renomeações

| Antes | Depois | Arquivo |
|---|---|---|
| `Bruno` (Goomba) | `Drone` | `entities/Drone.py` |
| `Tiago` (Koopa) | `HeavyBot` | `entities/HeavyBot.py` |
| `RedMushroom` | `WeaponPowerup` | `entities/WeaponPowerup.py` |
| `CoinBox` / `RandomBox` | `PowerBox` | `entities/PowerBox.py` |
| sprite `goomba-1/2/flat` | `drone-1/2/flat` | `sprites/Drone.json` |
| sprite `koopa-*` | `heavybot-*` | `sprites/HeavyBot.json` |
| `Level2-1/2/3.json` | `Phase1/2/3.json` | `levels/` |

---

## Sistemas Novos

### 1. Combate Corpo a Corpo — `traits/melee.py`

- **Ativação:** clique esquerdo do mouse
- **Direção:** na direção que Yasmin está virada (determinada por `goTrait.heading`)
- **Hitbox:** retângulo de 40×32 px à frente de Yasmin, ativo por 8 frames
- **Efeito:** inimigos dentro da hitbox recebem hit e knockback horizontal de 6 px na direção oposta
- **Cooldown:** 20 frames entre ataques (evita spam)
- **Visual:** reutiliza o frame `yasmin_break` (x=160, y=0 no spritesheet) como frame de ataque durante os 8 frames ativos; sem necessidade de novo sprite

### 2. Sistema de HP dos Inimigos

- Adicionado à `EntityBase`: atributo `hp` (int)
- `Drone`: `hp = 1` — morre no primeiro hit
- `HeavyBot`: `hp = 2` — precisa de 2 hits; ao levar o primeiro, muda de sprite (estado "danificado") e velocidade aumenta 20%
- Método `on_hit(direction)` na EntityBase: reduz hp, aplica knockback, triggera animação de dano (piscada de 10 frames)
- Ao `hp == 0`: comportamento de morte existente (timer + animação flat)

### 3. Powerup de Arma Temporária — `entities/WeaponPowerup.py`

- Substituí o cogumelo. Item visual sci-fi (ex: cristal de energia)
- Sprite: usa coordenadas de Items.png — item de estrela/cristal existente na spritesheet (a determinar na implementação conforme o visual do Items.png)
- Spawna de um `PowerBox` quando Yasmin bate por baixo (igual CoinBox atual)
- Yasmin coleta tocando o item
- **Efeito:** ativa `powerUpState = 1` por **10 segundos** (600 frames a 60fps)
- Durante powerup ativo:
  - Clique esquerdo dispara projétil horizontal (`entities/Projectile.py`) em vez de melee
  - Projétil viaja a 8 px/frame, mata qualquer inimigo que tocar (ignora HP, 1-shot)
  - Projétil some ao atingir parede ou sair da tela
- Dashboard mostra barra de tempo do powerup no canto superior direito
- Ao expirar: volta ao ataque melee

### 4. Projétil — `entities/Projectile.py`

- Entidade simples: `rect`, `vel_x`, `alive`
- Atualiza posição a cada frame
- Colisão com nível (tiles sólidos) → `alive = False`
- Colisão com inimigo → `on_hit()` no inimigo e `alive = False`
- Renderizado como `pygame.draw.circle` de 6px em amarelo/ciano (sem necessidade de spritesheet; cor a ajustar conforme tema)

### 5. Morte e Reinício de Fase

- `Yasmin` ganha dois flags distintos: `restart_phase` (reinicia fase atual) e `go_to_menu` (volta ao menu)
- Morte → `gameOver()` → seta `restart_phase = True` (não `go_to_menu`)
- `main.py` mantém `current_phase: str` (ex: `"Phase1"`) e um loop interno de fase:
  ```
  while True:
      level.loadLevel(current_phase)
      yasmin = Yasmin(...)
      resultado = game_loop()  # retorna 'restart', 'next', 'menu'
      if resultado == 'restart': continue
      if resultado == 'next': current_phase = próxima; continue
      if resultado == 'menu': break
  ```
- Não há sistema de vidas; tentativas ilimitadas

### 6. Tela de Vitória — `classes/VictoryScreen.py`

- Exibida após Yasmin tocar o portal final da Fase 3
- Mostra: "VOCÊ VENCEU!", pontuação final, tempo total
- Opção: `[ENTER] Menu` → volta ao menu principal
- Estrutura similar ao `LevelComplete` já existente

---

## Menu

- Mantém estrutura: JOGAR / OPÇÕES / SAIR
- **JOGAR:** carrega `Phase1.json` diretamente e inicia o jogo (sem tela de seleção)
- Remove: `chooseLevel()`, `drawLevelChooser()`, `drawBorder()`, `loadLevelNames()`, `inChoosingLevel` e todo código relacionado
- Manter: configurações de música e SFX

---

## Progressão de Fases

Fases ficam em `levels/Phase1.json`, `levels/Phase2.json`, `levels/Phase3.json`.  
Ao completar Phase1 → carrega Phase2; Phase2 → Phase3; Phase3 → VictoryScreen.

### Phase1 — Introdução

- **Comprimento:** 70 tiles
- **Objetivo:** aprender combate e plataformas móveis
- **Inimigos:** 4 Drones (hp=1), 0 HeavyBots
- **Plataformas móveis:** 1 sequência horizontal simples (amplitude 4 tiles, speed 1)
- **PowerBox:** 1 (posição central)
- **Estrutura:** chão plano com 2 buracos pequenos, plataforma móvel sobre o segundo buraco, inimigos espalhados, portal no final

### Phase2 — Progressão

- **Comprimento:** 90 tiles
- **Objetivo:** combinar combate e sequências de plataforma
- **Inimigos:** 4 Drones + 3 HeavyBots (hp=2)
- **Plataformas móveis:** 2 sequências (1 horizontal + 1 vertical), requerem timing
- **PowerBox:** 2
- **Estrutura:** seção inicial de combate, grande buraco com plataformas móveis, seção densa de inimigos, portal no final

### Phase3 — Desafio Final

- **Comprimento:** 110 tiles
- **Objetivo:** dominar todos os sistemas
- **Inimigos:** 3 Drones + 5 HeavyBots
- **Plataformas móveis:** 3 sequências (2 horizontais + 1 vertical), amplitudes maiores e speeds mais altos
- **PowerBox:** 2
- **Estrutura:** abertura com HeavyBots, corredor de plataformas móveis longas, área final com inimigos agrupados antes do portal

---

## Dashboard

- Remove: exibição de moedas
- Mantém: pontos, tempo, nome da fase
- Adiciona: barra de powerup (aparece só quando ativo, some ao expirar)

---

## Arquitetura de Arquivos — Alterações

```
traits/
  melee.py          ← NOVO
  
entities/
  Drone.py          ← RENOMEADO de Bruno.py
  HeavyBot.py       ← RENOMEADO de Tiago.py
  WeaponPowerup.py  ← SUBSTITUÍ RedMushroom.py
  PowerBox.py       ← SUBSTITUÍ CoinBox.py + RandomBox.py
  Projectile.py     ← NOVO
  Coin.py           ← DELETADO
  CoinBox.py        ← DELETADO
  CoinBrick.py      ← DELETADO

classes/
  VictoryScreen.py  ← NOVO
  Menu.py           ← MODIFICADO (remove seleção de nível)
  Level.py          ← MODIFICADO (remove addCoin, addCoinBox, addCoinBrick, addGoomba→addDrone, addKoopa→addHeavyBot, addRedMushroom→addWeaponPowerup)
  Dashboard.py      ← MODIFICADO (remove coins, adiciona powerup bar)

sprites/
  Drone.json        ← RENOMEADO de Bruno.json (atualiza nomes internos)
  HeavyBot.json     ← RENOMEADO de Koopa.json (atualiza nomes internos)
  WeaponPowerup.json← NOVO

levels/
  Phase1.json       ← NOVO (substitui Level2-1)
  Phase2.json       ← NOVO (substitui Level2-2)
  Phase3.json       ← NOVO (substitui Level2-3)
  Level1-1.json     ← DELETADO
  Level1-2.json     ← DELETADO
  Level2-1.json     ← DELETADO
  Level2-2.json     ← DELETADO
  Level2-3.json     ← DELETADO

main.py             ← MODIFICADO (controle de fase atual, reinício de fase, VictoryScreen)
```

---

## Fora do Escopo

- Não muda engine de física ou câmera
- Não muda sistema de colisão com nível
- Não muda sistema de som (reutiliza sons existentes)
- Não adiciona save/load de progresso
- Não adiciona novos tipos de tile no tileset
