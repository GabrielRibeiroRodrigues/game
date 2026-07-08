"""Cena do menu principal: JOGAR/CONTINUAR/COMO JOGAR/OPCOES/SAIR.

O submenu de opcoes controla musica/sons (liga/desliga e volume 0-10,
ajustado com as setas esquerda/direita) e persiste via SaveManager.
"""
import pygame

from core import fx as FX
from core.scene import Scene
from classes.Level import Level

ROW_START_Y = 253
ROW_SPACING = 40
DOT_X = 145
LABEL_X = 180
VALUE_X = 360


def _make_cursor(color: tuple) -> pygame.Surface:
    """Seta triangular simples desenhada em codigo (sem asset externo)."""
    surf = pygame.Surface((20, 20), pygame.SRCALPHA)
    pygame.draw.polygon(surf, color, [(2, 3), (2, 17), (17, 10)])
    return surf


class MenuScene(Scene):
    def __init__(self, screen: pygame.Surface, dashboard, sound, save) -> None:
        super().__init__()
        self.screen = screen
        self.dashboard = dashboard
        self.sound = sound
        self.save = save
        self.state = 0
        self.inSettings = False
        self.level = Level(screen, sound, dashboard)
        self.level.loadLevel("Phase1")
        self.menu_dot = _make_cursor((0, 220, 255))
        self.menu_dot2 = _make_cursor((70, 80, 100))

    # ---------- ciclo de vida ----------

    def on_enter(self) -> None:
        FX.reset()
        self.dashboard.state = "menu"
        self.dashboard.points = 0
        self.dashboard.time = 0
        self.dashboard.ticks = 0
        self.dashboard.yasmin = None
        if self.sound.music_on and not self.sound.music_playing():
            self.sound.play_music()

    # ---------- entradas do menu ----------

    def _main_entries(self):
        entries = [("JOGAR", self._start_new)]
        unlocked = self.save.progress["unlocked_phase"]
        if unlocked > 0:
            entries.append(
                ("CONTINUAR - FASE {}".format(unlocked + 1),
                 self._continue_game)
            )
        entries.append(("COMO JOGAR", self._open_howtoplay))
        entries.append(("OPCOES", self._open_settings))
        entries.append(("SAIR", self._quit))
        return entries

    def _settings_rows(self):
        return [
            ("MUSICA", "toggle_music"),
            ("VOL. MUSICA", "music_volume"),
            ("SONS", "toggle_sfx"),
            ("VOL. SONS", "sfx_volume"),
            ("VOLTAR", "back"),
        ]

    # ---------- acoes ----------

    def _start_new(self) -> None:
        self._start_at_phase(0)

    def _continue_game(self) -> None:
        self._start_at_phase(self.save.progress["unlocked_phase"])

    def _start_at_phase(self, phase_index: int) -> None:
        self.sound.stop_music()
        from ui.gameplay_scene import GameplayScene
        self.manager.switch(
            GameplayScene(self.screen, self.dashboard, self.sound,
                          self.save, phase_index=phase_index)
        )

    def _open_howtoplay(self) -> None:
        from ui.howtoplay_scene import HowToPlayScene
        self.manager.push(HowToPlayScene(self.screen))

    def _open_settings(self) -> None:
        self.inSettings = True
        self.state = 0

    def _quit(self) -> None:
        self.manager.quit()

    # ---------- eventos ----------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            if self.inSettings:
                self.inSettings = False
                self.state = 0
            else:
                self.manager.quit()
            return

        max_state = (len(self._settings_rows()) if self.inSettings
                     else len(self._main_entries())) - 1
        if event.key in (pygame.K_UP, pygame.K_k):
            self.state = max(0, self.state - 1)
        elif event.key in (pygame.K_DOWN, pygame.K_j):
            self.state = min(max_state, self.state + 1)
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT) and self.inSettings:
            self._adjust_volume(+1 if event.key == pygame.K_RIGHT else -1)
        elif event.key == pygame.K_RETURN:
            if self.inSettings:
                self._activate_settings_row()
            else:
                self._main_entries()[self.state][1]()

    def _adjust_volume(self, delta: int) -> None:
        _, kind = self._settings_rows()[self.state]
        if kind == "music_volume":
            self.sound.set_music_volume(self.sound.music_volume + delta)
            self.save.settings["music_volume"] = self.sound.music_volume
        elif kind == "sfx_volume":
            self.sound.set_sfx_volume(self.sound.sfx_volume + delta)
            self.save.settings["sfx_volume"] = self.sound.sfx_volume
            self.sound.play_sfx(self.sound.kick)  # feedback audivel
        else:
            return
        self.save.save_settings()

    def _activate_settings_row(self) -> None:
        _, kind = self._settings_rows()[self.state]
        if kind == "toggle_music":
            self.sound.music_on = not self.sound.music_on
            if self.sound.music_on:
                self.sound.play_music()
            else:
                self.sound.stop_music()
            self.save.settings["sound"] = self.sound.music_on
            self.save.save_settings()
        elif kind == "toggle_sfx":
            self.sound.allowSFX = not self.sound.allowSFX
            self.save.settings["sfx"] = self.sound.allowSFX
            self.save.save_settings()
        elif kind == "back":
            self.inSettings = False
            self.state = 0

    # ---------- frame ----------

    def run_frame(self, surface: pygame.Surface) -> None:
        self._drawBackground()
        self.dashboard.update()
        if self.inSettings:
            self._drawSettings()
        else:
            self._drawMenu()

    def _drawBackground(self) -> None:
        self.screen.blit(self.level.background, (0, 0))
        self.screen.blit(self.level.background, (self.level.bgWidth, 0))
        ground = self.level.sprites.spriteCollection.get("ground").image
        for y in range(13, 15):
            for x in range(0, 20):
                self.screen.blit(ground, (x * 32, y * 32))
        self.dashboard.drawText("CRAZY", 200, 100, 48)
        self.dashboard.drawText("WORLD", 200, 155, 48)
        sprites = self.level.sprites.spriteCollection
        self.screen.blit(sprites.get("yasmin_idle").image, (2 * 32, 12 * 32))
        self.screen.blit(sprites.get("drone-1").image,
                         (int(18.5 * 32), 12 * 32))
        best = self.save.progress["best_score"]
        if best > 0:
            self.dashboard.drawText(
                "RECORDE {:06d}".format(best), 240, 452, 14)

    def _drawDots(self, count: int) -> None:
        for i in range(count):
            dot = self.menu_dot if self.state == i else self.menu_dot2
            self.screen.blit(dot, (DOT_X, ROW_START_Y + i * ROW_SPACING))

    def _drawMenu(self) -> None:
        entries = self._main_entries()
        self._drawDots(len(entries))
        for i, (label, _) in enumerate(entries):
            self.dashboard.drawText(
                label, LABEL_X, ROW_START_Y + 7 + i * ROW_SPACING, 24)

    def _drawSettings(self) -> None:
        rows = self._settings_rows()
        self._drawDots(len(rows))
        for i, (label, kind) in enumerate(rows):
            y = ROW_START_Y + 7 + i * ROW_SPACING
            self.dashboard.drawText(label, LABEL_X, y, 24)
            if kind == "toggle_music":
                self.dashboard.drawText(
                    "SIM" if self.sound.music_on else "NAO", VALUE_X, y, 24)
            elif kind == "toggle_sfx":
                self.dashboard.drawText(
                    "SIM" if self.sound.allowSFX else "NAO", VALUE_X, y, 24)
            elif kind == "music_volume":
                self._drawVolumeBar(VALUE_X, y + 8, self.sound.music_volume)
            elif kind == "sfx_volume":
                self._drawVolumeBar(VALUE_X, y + 8, self.sound.sfx_volume)

    def _drawVolumeBar(self, x: int, y: int, volume: int) -> None:
        for i in range(10):
            color = (0, 200, 255) if i < volume else (60, 60, 80)
            pygame.draw.rect(self.screen, color, (x + i * 12, y, 8, 14))
