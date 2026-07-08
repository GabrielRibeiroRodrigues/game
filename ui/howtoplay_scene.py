"""Cena COMO JOGAR: controles e dicas."""
import pygame

from core.scene import Scene

CONTROLS = [
    ("MOVER",  "SETA ESQUERDA / DIREITA"),
    ("PULAR",  "ESPACO ou SETA CIMA (2x no ar)"),
    ("CORRER", "SEGURE SHIFT"),
    ("ATACAR", "CLIQUE ESQUERDO (3 cliques = combo)"),
    ("PAUSAR", "ESC ou F5"),
]
TIPS = [
    "Encadeie 3 golpes: o terceiro e mais forte.",
    "Pise nos inimigos para dana-los por cima.",
    "Toque no beacon para salvar seu progresso na fase.",
    "Destrua projeteis das torretas com seu golpe.",
    "Derrote o MEGA BOT na Fase 3 para abrir o portal.",
]


class HowToPlayScene(Scene):
    def __init__(self, screen: pygame.Surface) -> None:
        super().__init__()
        self.screen = screen
        self.font_title = pygame.font.SysFont("monospace", 30, bold=True)
        self.font_sec = pygame.font.SysFont("monospace", 18, bold=True)
        self.font_body = pygame.font.SysFont("monospace", 16)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and \
                event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.manager.pop()

    def run_frame(self, surface: pygame.Surface) -> None:
        w, h = self.screen.get_size()
        self.screen.fill((5, 10, 30))

        title = self.font_title.render("COMO JOGAR", True, (0, 220, 180))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, 30))
        pygame.draw.line(self.screen, (0, 180, 140), (60, 75), (w - 60, 75), 2)

        sec = self.font_sec.render("CONTROLES", True, (255, 220, 80))
        self.screen.blit(sec, (70, 95))
        for i, (action, key) in enumerate(CONTROLS):
            y = 125 + i * 30
            self.screen.blit(
                self.font_body.render(action, True, (200, 200, 255)), (90, y))
            self.screen.blit(
                self.font_body.render(key, True, (200, 200, 200)), (280, y))

        divider_y = 125 + len(CONTROLS) * 30 + 5
        pygame.draw.line(self.screen, (60, 60, 100),
                         (60, divider_y), (w - 60, divider_y), 1)

        tip_y = divider_y + 15
        sec2 = self.font_sec.render("DICAS", True, (255, 220, 80))
        self.screen.blit(sec2, (70, tip_y))
        for i, tip in enumerate(TIPS):
            surf = self.font_body.render("* " + tip, True, (180, 180, 180))
            self.screen.blit(surf, (90, tip_y + 30 + i * 28))

        hint = self.font_body.render(
            "Pressione ENTER ou ESC para voltar", True, (100, 100, 120))
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 35))
