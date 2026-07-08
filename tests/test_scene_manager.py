import pygame

from core.scene import Scene, SceneManager


class Recorder(Scene):
    def __init__(self, log, name):
        super().__init__()
        self.log = log
        self.name = name

    def on_enter(self):
        self.log.append(self.name + ":enter")

    def on_exit(self):
        self.log.append(self.name + ":exit")

    def handle_event(self, event):
        self.log.append(self.name + ":event")

    def run_frame(self, surface):
        self.log.append(self.name + ":frame")


def make_key_event():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)


def test_push_calls_on_enter_and_sets_manager():
    log = []
    m = SceneManager()
    scene = Recorder(log, "a")
    m.push(scene)
    assert scene.manager is m
    assert log == ["a:enter"]
    assert m.current is scene


def test_pop_calls_on_exit_and_reveals_previous():
    log = []
    m = SceneManager()
    a, b = Recorder(log, "a"), Recorder(log, "b")
    m.push(a)
    m.push(b)
    m.pop()
    assert m.current is a
    assert log == ["a:enter", "b:enter", "b:exit"]


def test_pop_last_scene_stops_manager():
    m = SceneManager()
    m.push(Recorder([], "a"))
    m.pop()
    assert not m.running


def test_switch_clears_stack():
    log = []
    m = SceneManager()
    m.push(Recorder(log, "a"))
    m.push(Recorder(log, "b"))
    m.switch(Recorder(log, "c"))
    assert log == ["a:enter", "b:enter", "b:exit", "a:exit", "c:enter"]
    assert len(m._stack) == 1
    assert m.running


def test_tick_routes_events_and_frame_to_top_only():
    log = []
    m = SceneManager()
    m.push(Recorder(log, "bottom"))
    m.push(Recorder(log, "top"))
    log.clear()
    m.tick([make_key_event()], surface=None)
    assert log == ["top:event", "top:frame"]


def test_quit_event_stops_manager_before_scene():
    log = []
    m = SceneManager()
    m.push(Recorder(log, "a"))
    log.clear()
    m.tick([pygame.event.Event(pygame.QUIT)], surface=None)
    assert not m.running
    assert log == []


def test_scene_change_mid_events_discards_remaining():
    log = []
    m = SceneManager()

    class Popper(Recorder):
        def handle_event(self, event):
            super().handle_event(event)
            self.manager.pop()

    m.push(Recorder(log, "bottom"))
    m.push(Popper(log, "popper"))
    log.clear()
    m.tick([make_key_event(), make_key_event()], surface=None)
    # popper trata 1 evento, sai; o 2o evento e descartado;
    # o frame roda na cena que sobrou (bottom)
    assert log == ["popper:event", "popper:exit", "bottom:frame"]


def test_tick_with_empty_stack_stops():
    m = SceneManager()
    m.tick([], surface=None)
    assert not m.running
