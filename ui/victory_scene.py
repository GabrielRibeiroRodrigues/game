"""Cena de vitoria apos a Fase 3."""
import pygame

from core.scene import Scene


class VictoryScene(Scene):
    def __init__(self, screen: pygame.Surface, dashboard, sound, save) -> None:
        super().__init__()
        self.screen = screen
        self.dashboard = dashboard
        self.sound = sound
        self.save = save
        self.font_big = pygame.font.SysFont("monospace", 48, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 24)

    def on_enter(self) -> None:
        self.is_record = self.dashboard.points > self.save.progress["best_score"]
        self.save.record_score(self.dashboard.points)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and \
                event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            from ui.menu_scene import MenuScene
            self.manager.switch(MenuScene(self.screen, self.dashboard,
                                          self.sound, self.save))

    def run_frame(self, surface: pygame.Surface) -> None:
        self.screen.fill((5, 10, 30))
        title = self.font_big.render("MISSAO COMPLETA!", True, (0, 255, 180))
        subtitle = self.font_small.render(
            "Pontos: {:06d}".format(self.dashboard.points), True,
            (200, 200, 200))
        hint = self.font_small.render(
            "ENTER para voltar ao menu", True, (120, 120, 120))
        w, h = self.screen.get_size()
        self.screen.blit(title, (w // 2 - title.get_width() // 2, h // 2 - 80))
        self.screen.blit(subtitle,
                         (w // 2 - subtitle.get_width() // 2, h // 2))
        if self.is_record:
            record = self.font_small.render(
                "NOVO RECORDE!", True, (255, 220, 80))
            self.screen.blit(record,
                             (w // 2 - record.get_width() // 2, h // 2 + 30))
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h // 2 + 60))
