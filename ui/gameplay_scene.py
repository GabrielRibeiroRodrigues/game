"""Cena de gameplay: roda as fases, morte/respawn e transicoes.

Substitui o antigo run_phase() bloqueante do main.py. A sequencia de morte
e uma sub-maquina de estados ("playing" | "dying") em vez do loop bloqueante
que existia dentro de Yasmin.gameOver().
"""
import pygame

from core import config
from core import fx as FX
from core.log import get_logger
from core.scene import Scene
from classes.Level import Level
from entities.Yasmin import Yasmin

log = get_logger(__name__)

PHASES = ["Phase1", "Phase2", "Phase3"]

DEATH_FRAMES = 130          # duracao da animacao de morte (~2s)
DEATH_MAX_RADIUS = 400      # raio inicial do circulo que fecha


class GameplayScene(Scene):
    def __init__(self, screen: pygame.Surface, dashboard, sound, save,
                 phase_index: int = 0) -> None:
        super().__init__()
        self.screen = screen
        self.dashboard = dashboard
        self.sound = sound
        self.save = save
        self.phase_index = phase_index
        self.checkpoint = None      # tile (x, y) do ultimo beacon ativado
        self.mode = "playing"       # "playing" | "dying"
        self.death_timer = 0
        self.level = None
        self.yasmin = None

    # ---------- ciclo de vida ----------

    def on_enter(self) -> None:
        self.sound.stop_music()
        self._load_phase()

    def _load_phase(self) -> None:
        self.mode = "playing"
        self.save.record_phase_reached(self.phase_index)
        phase_name = PHASES[self.phase_index]
        phase_display = str(self.phase_index + 1)

        self.level = Level(self.screen, self.sound, self.dashboard)
        self.level.loadLevel(phase_name)

        self.dashboard.state = "start"
        self.dashboard.time = 0
        self.dashboard.ticks = 0
        self.dashboard.levelName = phase_display

        self.yasmin = Yasmin(0, 0, self.level, self.screen,
                             self.dashboard, self.sound)
        self.dashboard.yasmin = self.yasmin

        if self.checkpoint is not None:
            tile = config.TILE_SIZE
            self.yasmin.setPos(self.checkpoint[0] * tile,
                               (self.checkpoint[1] - 1) * tile)
            self.yasmin.checkpoint = self.checkpoint
            for ent in self.level.entityList:
                if ent.type == "Checkpoint" and ent.tile_pos == self.checkpoint:
                    ent.activated = True
        self.yasmin.camera.snap()

        FX.reset()
        FX.phase_banner("FASE " + phase_display)
        FX.fade_in(30)

    # ---------- eventos ----------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.mode != "playing":
            return
        if event.type == pygame.KEYDOWN and \
                event.key in (pygame.K_ESCAPE, pygame.K_F5):
            from ui.pause_scene import PauseScene
            self.manager.push(PauseScene(self.screen, self.dashboard,
                                         self.sound, self.save))
            return
        self.yasmin.input.process_event(event)

    # ---------- frame ----------

    def run_frame(self, surface: pygame.Surface) -> None:
        if self.mode == "dying":
            self._run_death_frame()
            return

        self.level.drawLevel(self.yasmin.camera)
        self.yasmin.update()
        FX.update()
        FX.draw_world(self.screen, self.yasmin.camera)
        self.dashboard.update()

        if self.yasmin.dead:
            self._start_death()
        elif self.level.checkEndPortal(self.yasmin.rect):
            self._next_phase()

    # ---------- morte / respawn ----------

    def _start_death(self) -> None:
        self.mode = "dying"
        self.death_timer = DEATH_FRAMES
        self.sound.stop_music(0)
        # jingle de morte toca mesmo com musica desligada (feedback, nao trilha)
        self.sound.music_channel.play(self.sound.death)

    def _run_death_frame(self) -> None:
        """Circulo fechando sobre o ultimo frame do mundo (nao-bloqueante)."""
        self.death_timer -= 1
        radius = max(12, int(DEATH_MAX_RADIUS * self.death_timer / DEATH_FRAMES))
        overlay = pygame.Surface(config.INTERNAL_SIZE)
        overlay.set_colorkey((255, 255, 255), pygame.RLEACCEL)
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        center = (int(self.yasmin.camera.x + self.yasmin.rect.x) + 16,
                  self.yasmin.rect.y + 16)
        pygame.draw.circle(overlay, (255, 255, 255), center, radius)
        self.screen.blit(overlay, (0, 0))
        if self.death_timer <= 0:
            self._respawn()

    def _respawn(self) -> None:
        self.checkpoint = self.yasmin.checkpoint
        self._load_phase()

    # ---------- progressao ----------

    def _next_phase(self) -> None:
        self.checkpoint = None
        self.phase_index += 1
        if self.phase_index >= len(PHASES):
            from ui.victory_scene import VictoryScene
            self.manager.switch(VictoryScene(self.screen, self.dashboard,
                                             self.sound, self.save))
        else:
            self._load_phase()
