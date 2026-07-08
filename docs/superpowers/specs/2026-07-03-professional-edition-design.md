# Crazy World — Edição Profissional

**Data:** 2026-07-03
**Status:** Aprovado pelo usuário
**Foco:** Game feel/polish + profundidade de gameplay (escolha do usuário). Abordagem: polish sobre a engine atual, sem refactor estrutural.

---

## Visão Geral

O jogo funciona, mas parece amador: sem feedback visual/sonoro nos acertos, morte em 1 toque, sem checkpoints, combate raso (1 golpe repetido), sem chefe, janela minúscula. Esta edição adiciona um sistema central de efeitos (FX), HP com checkpoints, combate com combo e stomp, um inimigo novo (Sentry), um chefe final (Mega Bot) e renderização em escala 2x — mantendo a arquitetura existente (`traits/`, `entities/`, `classes/`).

---

## 1. Renderização 2x e apresentação central (`classes/Screen.py`)

**Problema atual:** tudo desenha direto na janela 640×480 e `pygame.display.update()` está espalhado por Menu, Yasmin.gameOver, Pause etc.

**Solução:** novo módulo `classes/Screen.py` com uma classe `Renderer`:

- Cria a janela em **1280×960** e uma **surface interna de 640×480**.
- Todo o código existente continua recebendo a surface interna como `screen` — nenhuma classe de jogo muda sua forma de desenhar.
- `renderer.present()`: escala a surface interna 2x para a janela (`pygame.transform.scale`), aplica offset de screen shake (frame inteiro), aplica overlay de fade se houver transição ativa, e chama `pygame.display.flip()`.
- Todos os `pygame.display.update()` espalhados são substituídos por `renderer.present()` (o Renderer é acessível globalmente via módulo, ex: `Screen.get_renderer()`, para não ter que passar por todas as classes).
- Mouse: o Input só usa botões (não posição), então não há mapeamento de coordenadas a fazer.

## 2. Sistema de FX (`classes/FX.py`)

Módulo global (estado de módulo + funções, acessível de qualquer entidade sem injeção de dependência) com:

### Partículas (procedurais, `pygame.draw`)
- **Poeira**: ao aterrissar de um pulo, ao iniciar dash, ao virar de direção correndo. Círculos pequenos cinza que sobem e somem (~20 frames).
- **Faíscas de acerto**: 6–10 partículas amarelas/brancas irradiando do ponto de impacto do melee.
- **Explosão de morte**: 12–16 fragmentos coloridos (cor do inimigo) com gravidade, ao matar qualquer inimigo.
- **Rastro de projétil**: partículas pequenas atrás do projétil da jogadora.
- API: `FX.dust(x, y)`, `FX.hit_sparks(x, y, direction)`, `FX.explosion(x, y, color)`, etc. Partículas guardam posição em coordenadas de mundo; o update/draw recebe a câmera.

### Screen shake
- `FX.shake(frames, magnitude)` — acertos de melee: (4, 2); morte de inimigo: (6, 3); impactos do chefe: (12, 5).
- O Renderer lê o shake ativo em `present()` e desloca o frame inteiro por um offset aleatório dentro da magnitude.

### Hit-stop
- `FX.hitstop(frames)` — congela o jogo por N frames (golpe conecta: 3; golpe final do combo/kill: 5).
- Implementação no loop de `run_phase`: enquanto `FX.hitstop_remaining > 0`, decrementa, não chama updates, apenas re-apresenta o frame anterior e tica o clock.

### Texto flutuante
- `FX.float_text("100", x, y)` — substitui o desenho manual de "100"/"200" em `Drone._onDead` / `HeavyBot._onDead`. Sobe e desvanece em ~40 frames.

### Flash branco em hit-stun
- Inimigos em `hit_stun` são desenhados com overlay branco (surface do sprite com `fill((255,255,255), special_flags=BLEND_RGB_ADD)`) alternando a cada 2 frames, em vez do piscar atual (que some com o sprite).

### Transições e banner de fase
- `FX.fade_out(frames)` / `FX.fade_in(frames)` — overlay preto com alpha animado, aplicado pelo Renderer. Usado: menu→fase, morte→respawn, fase→fase, fase→vitória.
- `FX.phase_banner("FASE 1")` — texto grande que desliza da esquerda, segura ~60 frames no centro, sai pela direita. Mostrado no início/respawn de cada fase.

## 3. HP da jogadora + Checkpoints

### Corações
- `Yasmin.hearts = 3`, `max_hearts = 3` (reset em cada spawn).
- Tocar em inimigo (colisão que hoje chama `gameOver()`): perde 1 coração, knockback horizontal para longe do inimigo + pequeno pulo, `invincibilityFrames = 90` (Yasmin pisca durante), som de dano (`bump.ogg`).
- Projétil de Sentry e ataques do chefe causam o mesmo dano de 1 coração.
- Com 0 corações → sequência de morte atual (círculo fechando) → respawn no checkpoint.
- **Cair em buraco = morte instantânea** (independe de corações).
- HUD: 3 corações desenhados proceduralmente (dois círculos + triângulo, vermelho/cinza) no canto superior esquerdo do Dashboard, abaixo dos pontos.

### Checkpoints
- Novo entity no JSON de fase: `"Checkpoint": [[x, y]]` — 1 por fase, no meio.
- Nova entidade `entities/Checkpoint.py` (`type = "Checkpoint"`): beacon desenhado proceduralmente (poste + luz). Inativo: luz cinza; ativo: luz verde pulsante + partículas.
- Ao tocar: ativa (som `powerup_appears.ogg`), grava o ponto de respawn.
- **Fluxo de morte:** `run_phase` retorna `"restart"`; `main.py` recarrega a fase e spawna a Yasmin **na posição do checkpoint ativado** (se houver), **mantendo `dashboard.points`** e restaurando 3 corações. Sem checkpoint ativado, respawn no início. A tela GameOverScreen atual é substituída por um fade rápido (a morte não deve ser burocrática).
- O estado "checkpoint ativado da fase atual" vive em `main.py` (dicionário simples por fase) e é zerado ao trocar de fase ou voltar ao menu.

## 4. Combate mais rico

### Combo de 3 golpes (`traits/melee.py` reescrito)
- Estados: `idle → attack1 → attack2 → attack3 → cooldown`.
- Cada golpe: hitbox ativa por 8 frames (mesma geometria atual: 28×24 à frente).
- **Janela de encadeamento:** clicar de novo até 14 frames após o fim do golpe atual encadeia o próximo.
- Golpes 1 e 2: 1 de dano, knockback 4. **Golpe 3: 2 de dano, knockback 8 + pop vertical no inimigo (`vel.y = -4`), hit-stop 5, shake maior.**
- Após o golpe 3 (ou janela perdida): cooldown de 20 frames.
- Cada golpe que conecta: `FX.hit_sparks` + `FX.hitstop(3)` + `FX.shake(4, 2)`.
- Um inimigo só pode ser atingido 1x por golpe (guardar conjunto de entidades já atingidas no golpe atual — corrige o bug atual de `on_hit` ser chamado todo frame da hitbox).
- `EntityBase.on_hit(direction, damage=1)` ganha parâmetro de dano.

### Stomp
- Em `_onCollisionWithMob`: se a Yasmin está caindo (`vel.y > 0`) e a parte de baixo dela está acima do centro do inimigo → é stomp: 1 de dano no inimigo, `bounceTrait` ativado (já existe), som `stomp.ogg`, FX de faíscas. Caso contrário, é dano na Yasmin (seção 3).

### Knockback melhorado
- `on_hit` aplica também `vel.y = -2` (pop vertical leve) nos golpes 1–2, `-4` no golpe 3.

## 5. Inimigo novo: Sentry (`entities/Sentry.py`)

- `type = "Mob"`, `hp = 2`, **estacionária** (sem LeftRightWalkTrait), afetada por gravidade.
- Visual: procedural — base + cúpula + canhão que aponta para a direção da jogadora (retângulos/círculos nas cores do tema; sem sprite novo).
- **Comportamento:** quando a Yasmin está a até 8 tiles de distância horizontal e ±2 tiles vertical, carrega por 45 frames (luz piscando = telegraph) e dispara um projétil inimigo na direção dela. Recarga de 75 frames.
- **Projétil inimigo:** reutiliza `entities/Projectile.py` com parâmetro `owner` (`"player"` | `"enemy"`); versão inimiga é vermelha, velocidade 3 px/frame, causa 1 coração de dano na Yasmin, é destruída por melee (hitbox do golpe destrói projéteis inimigos com faíscas) e por paredes.
- Projéteis da jogadora matam a Sentry normalmente. Stomp na Sentry funciona (1 dano).
- JSON: `"Sentry": [[x, y]]`. Pontos ao matar: 200.

## 6. Chefe final: Mega Bot (`entities/Boss.py`)

- Colocado na arena final da Phase3 (JSON: `"Boss": [[x, y]]`). A arena é um trecho plano de ~20 tiles no fim da fase.
- **Corpo:** 64×64 px (2×2 tiles), desenhado proceduralmente (versão maior e mais ameaçadora do HeavyBot: corpo blindado, olho vermelho). `hp = 12`, `type = "Mob"` com flag `is_boss = True`.
- **Barra de HP:** quando o chefe está vivo e a Yasmin está na arena, o Dashboard desenha barra grande no topo central ("MEGA BOT" + barra vermelha proporcional ao HP).
- **Máquina de estados:**
  - `IDLE` (60 frames): parado, rastreia a jogadora.
  - `CHARGE`: telegraph de 30 frames (treme + olho pisca), depois investida horizontal a 5 px/frame até bater na parede da arena → `STUNNED` por 45 frames. O chefe recebe dano de melee/projétil em qualquer estado; o stun é uma janela segura para atacar (ele não se move nem causa dano de contato por investida durante o stun), não um requisito.
  - `JUMP_SLAM`: pula (vel.y = -16) na direção da jogadora; ao aterrissar: `FX.shake(12, 5)`, shockwave de partículas e **onda de choque** rasante (2 projéteis de chão, um para cada lado, 4 px/frame, pulável) que causa 1 de dano.
  - Alterna CHARGE/JUMP_SLAM com IDLE entre eles.
  - **Abaixo de 6 HP (fase 2):** IDLE cai para 30 frames, velocidade da investida 7 px/frame, e ao cruzar o limiar invoca 2 Drones (1x apenas).
- **Contato com o corpo:** 1 coração de dano na Yasmin (com knockback forte).
- **Morte:** sequência de ~90 frames de explosões em pontos aleatórios do corpo + shake contínuo → some → **portal de vitória aparece** (o EndPortal da Phase3 existe no JSON dentro da arena, mas fica invisível e sem colisão até a morte do chefe; a partir daí é desenhado e passa a contar em `checkEndPortal`). +1000 pontos.
- Stomp no chefe **não** causa dano (quica a Yasmin sem dano para ela) — o combate é de melee/projétil.

## 7. Rebalanceamento das fases

- **Phase1:** posições atuais mantidas + 1 Checkpoint no meio. Sem Sentry.
- **Phase2:** +2 Sentries em posições que cubram trechos de plataforma; 1 Checkpoint.
- **Phase3:** +2 Sentries; 1 Checkpoint antes da arena do chefe; arena plana de ~20 tiles no fim com o Boss; EndPortal reposicionado dentro da arena (ativado só após o chefe morrer).
- Revisão leve de densidade de inimigos considerando que a jogadora agora tem 3 corações (pode aumentar um pouco onde estava fácil demais).

## 8. HUD (Dashboard)

- Mantém: pontos, fase, tempo, barra de arma.
- Adiciona: corações (seção 3), barra de HP do chefe (seção 6).
- `Drone`/`HeavyBot` param de desenhar o texto de pontos manualmente — usam `FX.float_text`.

## Arquivos — resumo de mudanças

```
classes/
  Screen.py        ← NOVO (Renderer: janela 2x, present(), shake, fade)
  FX.py            ← NOVO (partículas, hitstop, float text, banner, transições)
  Dashboard.py     ← MOD (corações, barra do chefe)
  Camera.py        ← sem mudança (shake é no Renderer)
  Menu.py          ← MOD (present() em vez de display.update)
  Pause.py, GameOverScreen.py, VictoryScreen.py, LevelComplete.py, HowToPlay.py
                   ← MOD (present(); GameOverScreen deixa de ser usada na morte)
  Level.py         ← MOD (carrega Checkpoint/Sentry/Boss; spawn da Yasmin no checkpoint)

traits/
  melee.py         ← REESCRITO (combo de 3 golpes)

entities/
  EntityBase.py    ← MOD (on_hit com damage, pop vertical)
  Checkpoint.py    ← NOVO
  Sentry.py        ← NOVO
  Boss.py          ← NOVO
  Projectile.py    ← MOD (owner player/enemy)
  Yasmin.py        ← MOD (hearts, take_damage, stomp, FX, combo)
  Drone.py / HeavyBot.py ← MOD (float_text, flash branco, FX de morte)

levels/
  Phase1/2/3.json  ← MOD (Checkpoint, Sentry, Boss, arena)

main.py            ← MOD (Renderer, hitstop no loop, respawn em checkpoint,
                          transições, banner de fase)

tests/             ← NOVO (pytest)
  test_melee_combo.py    (máquina de estados do combo, janelas, dano por golpe)
  test_player_damage.py  (hearts, invencibilidade, morte, stomp vs dano)
  test_checkpoint.py     (seleção de ponto de respawn)
  test_fx_logic.py       (timers de partícula/hitstop/fade — sem renderização)
```

## Fora do escopo

- Fases novas (continuam 3), save de progresso, seleção de fase.
- Refactor da engine (física, colisão, câmera permanecem).
- Sprites desenhados à mão — todos os visuais novos são procedurais.
- Música nova (reutiliza sons existentes).

## Critérios de sucesso

1. Cada acerto de melee tem resposta visível e audível (hit-stop, faíscas, shake, som).
2. Morrer nunca joga o jogador para o início da fase se ele passou pelo checkpoint.
3. O chefe é derrotável, legível (telegraphs claros) e exige uso do combate.
4. Nenhuma regressão: as 3 fases continuam completáveis do menu à tela de vitória.
5. `pytest` verde na lógica de combate/dano/checkpoint.
