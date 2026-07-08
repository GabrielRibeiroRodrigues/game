"""Scene Manager: cenas nao-bloqueantes com um unico event loop.

Cada tela do jogo (menu, gameplay, pause, vitoria...) e uma Scene. O
SceneManager mantem uma pilha; apenas a cena do topo recebe eventos e roda
seu frame. Cenas de overlay (ex.: pause) tiram um snapshot da tela ao
entrar, entao nao ha necessidade de desenhar a pilha inteira.

Contrato de Scene:
- handle_event(event): eventos discretos (teclas, mouse). QUIT e tratado
  pelo manager antes de chegar aqui.
- run_frame(surface): atualiza E desenha um frame. (Nesta base de codigo
  update e draw das entidades sao entrelacados por design herdado; a cena
  espelha isso honestamente em um unico metodo.)
- on_enter()/on_exit(): hooks de ciclo de vida.

Transicoes dentro de handle_event/run_frame sao seguras: passam a valer no
frame seguinte.
"""
from typing import List, Optional

import pygame


class Scene:
    def __init__(self) -> None:
        self.manager: Optional["SceneManager"] = None

    def on_enter(self) -> None:
        """Chamado quando a cena entra no topo da pilha."""

    def on_exit(self) -> None:
        """Chamado quando a cena sai da pilha."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Recebe um evento discreto (a cena do topo apenas)."""

    def run_frame(self, surface: pygame.Surface) -> None:
        """Atualiza e desenha um frame da cena."""


class SceneManager:
    def __init__(self) -> None:
        self._stack: List[Scene] = []
        self.running: bool = True

    @property
    def current(self) -> Optional[Scene]:
        return self._stack[-1] if self._stack else None

    def push(self, scene: Scene) -> None:
        scene.manager = self
        self._stack.append(scene)
        scene.on_enter()

    def pop(self) -> Optional[Scene]:
        if not self._stack:
            return None
        scene = self._stack.pop()
        scene.on_exit()
        if not self._stack:
            self.running = False
        return scene

    def switch(self, scene: Scene) -> None:
        """Esvazia a pilha e entra na cena dada (troca de tela completa)."""
        while self._stack:
            self._stack.pop().on_exit()
        self.running = True
        self.push(scene)

    def quit(self) -> None:
        self.running = False

    def tick(self, events: List[pygame.event.Event],
             surface: pygame.Surface) -> None:
        """Roda um frame: eventos para a cena do topo, depois o frame dela."""
        scene = self.current
        if scene is None:
            self.running = False
            return
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            scene.handle_event(event)
            if self.current is not scene or not self.running:
                break  # cena mudou no meio dos eventos: descarta o restante
        scene = self.current
        if scene is not None and self.running:
            scene.run_frame(surface)
