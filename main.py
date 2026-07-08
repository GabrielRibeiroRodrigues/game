"""Bootstrap do Crazy World: inicializa pygame, renderer e o SceneManager.

Unico dono do event queue e do clock. Todo o fluxo de telas vive nas cenas
de ui/ (menu, gameplay, pause, como jogar, vitoria).
"""
import pygame

from core import config
from core import fx as FX
from core import screen as Screen
from core.audio import AudioManager
from core.save import SaveManager
from core.scene import SceneManager
from ui.dashboard import Dashboard
from ui.menu_scene import MenuScene


def main() -> None:
    pygame.mixer.pre_init(44100, -16, 2, 4096)
    pygame.init()
    Screen.init()
    screen = Screen.get_surface()
    pygame.display.set_caption("Crazy World")

    save = SaveManager()
    sound = AudioManager(save.settings)
    dashboard = Dashboard(screen=screen)

    manager = SceneManager()
    manager.push(MenuScene(screen, dashboard, sound, save))

    clock = pygame.time.Clock()
    while manager.running:
        events = pygame.event.get()
        if FX.hitstop_active():
            # congela o jogo re-apresentando o ultimo frame; so QUIT passa
            FX.tick_hitstop()
            for event in events:
                if event.type == pygame.QUIT:
                    manager.quit()
        else:
            manager.tick(events, screen)
        Screen.present()
        clock.tick(config.FPS)
        pygame.display.set_caption(
            "Crazy World - {:d} FPS".format(int(clock.get_fps()))
        )
    pygame.quit()


if __name__ == "__main__":
    main()
