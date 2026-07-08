# Design: Remoção de sprites do Mario + Correção de MovingPlatform

**Data:** 2026-07-05  
**Branch:** feature/edicao-profissional  

## Objetivo

Remover entidades e arquivos de sprite herdados do Mario que não são usados nas fases ativas, substituir o visual do PowerBox por desenho procedural próprio, e corrigir dois bugs no MovingPlatform (overshoot de amplitude e duplo deslocamento do jogador).

---

## Tarefa 1 — Remoção de código morto

### Arquivos a deletar

| Arquivo | Motivo |
|---------|--------|
| `entities/Bruno.py` | Inimigo goomba, não instanciado em nenhuma fase |
| `entities/Tiago.py` | Inimigo koopa, não instanciado em nenhuma fase |
| `entities/Mushroom.py` | RedMushroom, não instanciado em nenhuma fase |
| `entities/Coin.py` | Não instanciado em nenhuma fase |
| `entities/CoinBox.py` | Não instanciado em nenhuma fase (PowerBox é usado no lugar) |
| `entities/CoinBrick.py` | Não instanciado em nenhuma fase |
| `entities/RandomBox.py` | Não instanciado em nenhuma fase |
| `entities/Item.py` | Usado apenas por CoinBox (morto acima) |
| `sprites/Goomba.json` | Nunca carregado em `Sprites.py` |
| `sprites/RedMushroom.json` | Sprite `mushroom` não referenciado em nenhuma entidade ativa |

### Arquivos a renomear

| De | Para | Motivo |
|----|------|--------|
| `sprites/Bruno.json` | `sprites/Drone.json` | Contém sprites `drone-1`, `drone-2`, `drone-flat` do inimigo Drone |
| `sprites/Koopa.json` | `sprites/HeavyBot.json` | Contém sprites `heavybot-1`, `heavybot-2`, etc. do HeavyBot |

### Arquivos a modificar

**`classes/Sprites.py`** — atualizar a lista de JSONs carregados:
- Remover `./sprites/RedMushroom.json`
- Substituir `./sprites/Bruno.json` por `./sprites/Drone.json`
- Substituir `./sprites/Koopa.json` por `./sprites/HeavyBot.json`

---

## Tarefa 2 — Visual do PowerBox

O `PowerBox` atualmente usa a animação `CoinBox` oriunda do `tiles.png` (spritesheet do Mario). Será substituído por desenho procedural com `pygame.draw`, sem novos arquivos de asset.

### Estados visuais

**Ativo** (não triggerado):
- Fill: `#0a1a2e` (azul escuro)
- Borda: `#00BFFF` (ciano), 2px
- Texto `?` centralizado, branco, fonte `arial` tamanho 20 bold
- Pulsação: borda alterna entre ciano e `#005f8f` a cada 20 frames

**Triggerado** (após ser ativado):
- Fill: `#1a1a2a` (cinza escuro)
- Borda: `#333333`, 2px
- Sem texto

### Implementação

- Adicionar método `_draw(cam)` em `PowerBox` com `pygame.draw.rect` e `pygame.font.SysFont("arial", 20, bold=True)`
- Substituir os dois `self.screen.blit(...)` do `update()` por `self._draw(cam)`
- Manter intacta a animação de bounce (subir/descer 10px via `self.time` / `self.vel_anim`)
- Remover referência a `self.animation` e ao `spriteCollection.get("CoinBox")`

A referência a `CoinBox` em `Animations.json` pode ser mantida ou removida — como `CoinBox` entity foi deletada e `PowerBox` não usa mais, ela vira dead data no JSON. Remover para consistência.

---

## Tarefa 3 — Correção do MovingPlatform

### Bug 1: Overshoot de amplitude (plataforma entra em blocos)

**Causa:** `vel *= -1` ocorre depois que o rect já ultrapassou o limite. Na iteração seguinte a plataforma parte do lado errado.

**Fix em `MovingPlatform.update()`:**

```python
# horizontal
self.rect.x += self.vel
if abs(self.rect.x - self.startX) >= self.amplitude:
    self.vel *= -1
    self.rect.x = self.startX + self.amplitude * (1 if self.rect.x > self.startX else -1)

# vertical
self.rect.y += self.vel
if abs(self.rect.y - self.startY) >= self.amplitude:
    self.vel *= -1
    self.rect.y = self.startY + self.amplitude * (1 if self.rect.y > self.startY else -1)
```

### Bug 2: Duplo deslocamento (plataforma aparece mais rápida com jogador em cima)

**Causa:** `Level.updateEntities()` move `player.rect.x` diretamente via `+= platform.vel`. Em seguida, `yasmin.update()` chama `moveYasmin()` que aplica `vel.x` separadamente. O `checkX()` do Collider não compensa o deslocamento já aplicado, resultando em movimento inconsistente.

**Fix em `Level.updateEntities()`:**

Substituir atribuição direta ao rect por adição à velocidade do jogador:

```python
# antes
if platform.direction == "horizontal":
    player.rect.x += platform.vel
else:
    player.rect.y += platform.vel

# depois
if platform.direction == "horizontal":
    player.vel.x += platform.vel
else:
    player.vel.y += platform.vel
```

Assim `moveYasmin()` aplica tudo em uma única passagem e o `checkX()` / `checkY()` ainda pode corrigir colisões de tile normalmente.

---

## Fora do escopo

- Substituição dos tiles de fundo (`ground`, `ground_dirt`, `bush_*`) que também vêm do `tiles.png` — esses são estruturais e exigem novo tileset próprio
- Ajustes no layout das fases além dos bugs de plataforma reportados
- Novos assets de imagem para qualquer entidade
