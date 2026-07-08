"""Input do jogador.

Eventos discretos (cliques) chegam via process_event(), entregues pela cena
de gameplay — o event queue pertence exclusivamente ao loop principal.
Estado continuo (setas/pulo/boost) e lido por frame em update().
"""
import pygame
from pygame.locals import (
    K_LEFT, K_RIGHT, K_SPACE, K_UP, K_LSHIFT, K_h, K_k, K_l,
)


class Input:
    def __init__(self, entity) -> None:
        self.entity = entity

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.entity.powerup_active:
                self.entity.fireProjectile()
            else:
                self.entity.meleeTrait.trigger()

    def update(self) -> None:
        pressedKeys = pygame.key.get_pressed()

        if pressedKeys[K_LEFT] or pressedKeys[K_h] and not pressedKeys[K_RIGHT]:
            self.entity.traits["goTrait"].direction = -1
        elif pressedKeys[K_RIGHT] or pressedKeys[K_l] and not pressedKeys[K_LEFT]:
            self.entity.traits["goTrait"].direction = 1
        else:
            self.entity.traits["goTrait"].direction = 0

        isJumping = pressedKeys[K_SPACE] or pressedKeys[K_UP] or pressedKeys[K_k]
        self.entity.traits["jumpTrait"].jump(isJumping)

        self.entity.traits["goTrait"].boost = pressedKeys[K_LSHIFT]
