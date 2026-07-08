"""Cena de pause: overlay sobre um snapshot borrado do gameplay."""
import pygame

from core import screen as Screen
from core.scene import Scene
from ui.menu_scene import _make_cursor

OPTIONS = 2  # CONTINUAR / MENU


class PauseScene(Scene):
    def __init__(self, screen: pygame.Surface, dashboard, sound, save) -> None:
        super().__init__()
        self.screen = screen
        self.dashboard = dashboard
        self.sound = sound
        self.save = save
        self.state = 0
        self.snapshot = None
        self.dot = _make_cursor((0, 220, 255))
        self.gray_dot = _make_cursor((70, 80, 100))

    def on_enter(self) -> None:
        # a surface interna ainda contem o ultimo frame do gameplay
        self.snapshot = Screen.blur_surface(self.screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.manager.pop()
        elif event.key == pygame.K_UP and self.state > 0:
            self.state -= 1
        elif event.key == pygame.K_DOWN and self.state < OPTIONS - 1:
            self.state += 1
        elif event.key == pygame.K_RETURN:
            if self.state == 0:  # CONTINUAR
                self.manager.pop()
            else:                # MENU
                from ui.menu_scene import MenuScene
                self.manager.switch(MenuScene(self.screen, self.dashboard,
                                              self.sound, self.save))

    def run_frame(self, surface: pygame.Surface) -> None:
        self.screen.blit(self.snapshot, (0, 0))
        self.dashboard.drawText("PAUSADO", 100, 160, 68)
        self.dashboard.drawText("CONTINUAR", 150, 280, 32)
        self.dashboard.drawText("MENU", 150, 320, 32)
        positions = [275, 315]
        for i, y in enumerate(positions):
            dot = self.dot if self.state == i else self.gray_dot
            self.screen.blit(dot, (100, y))
