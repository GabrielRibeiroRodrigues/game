"""Renderer central: janela 2x, surface interna e present() unico.

Contrato: todo o codigo do jogo desenha na surface interna de 640x480
(obtida via get_surface()); present() aplica overlays do FX (banner/fade),
escala para a janela com o offset de screen shake e da flip. Nenhum outro
modulo deve chamar pygame.display.flip/update.
"""
import pygame

from core import config
from core import fx as FX

_renderer = None


class Renderer:
    def __init__(self) -> None:
        width, height = config.INTERNAL_SIZE
        self.window: pygame.Surface = pygame.display.set_mode(
            (width * config.WINDOW_SCALE, height * config.WINDOW_SCALE)
        )
        self.surface: pygame.Surface = pygame.Surface(config.INTERNAL_SIZE).convert()

    def present(self) -> None:
        FX.draw_screen(self.surface)
        offset = FX.get_shake_offset()
        scaled = pygame.transform.scale(self.surface, self.window.get_size())
        self.window.fill((0, 0, 0))
        self.window.blit(
            scaled,
            (offset[0] * config.WINDOW_SCALE, offset[1] * config.WINDOW_SCALE),
        )
        pygame.display.flip()


def init() -> Renderer:
    global _renderer
    _renderer = Renderer()
    return _renderer


def get_surface() -> pygame.Surface:
    return _renderer.surface


def present() -> None:
    _renderer.present()


def blur_surface(surface: pygame.Surface, factor: int = 8) -> pygame.Surface:
    """Blur barato por downscale/upscale (substitui o gaussian do scipy)."""
    width, height = surface.get_size()
    small = pygame.transform.smoothscale(
        surface, (max(1, width // factor), max(1, height // factor))
    )
    return pygame.transform.smoothscale(small, (width, height))
