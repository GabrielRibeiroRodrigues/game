"""AudioManager: musica e SFX com volume 0-10, mute e fades.

Substitui classes/Sound.py mantendo a mesma interface consumida pelo jogo
(atributos de sons, music_channel/sfx_channel, play_sfx, allowSFX), e
adicionando controle de volume persistente e fade in/out de musica.
"""
from pygame import mixer

MAX_VOLUME = 10
GAIN_PER_UNIT = 0.04  # volume 5 -> ganho 0.2 (comportamento historico)
MUSIC_FADE_IN_MS = 800
MUSIC_FADE_OUT_MS = 400


def volume_to_gain(volume: int) -> float:
    """Converte volume 0-10 no ganho 0.0-0.4 do canal (clampado)."""
    volume = max(0, min(MAX_VOLUME, int(volume)))
    return volume * GAIN_PER_UNIT


class AudioManager:
    def __init__(self, settings: dict) -> None:
        self.music_channel = mixer.Channel(0)
        self.sfx_channel = mixer.Channel(1)

        self.music_on = bool(settings.get("sound", True))
        self.allowSFX = bool(settings.get("sfx", True))
        self.music_volume = int(settings.get("music_volume", 5))
        self.sfx_volume = int(settings.get("sfx_volume", 5))

        self.soundtrack = mixer.Sound("./sfx/main_theme.ogg")
        self.coin = mixer.Sound("./sfx/coin.ogg")
        self.bump = mixer.Sound("./sfx/bump.ogg")
        self.stomp = mixer.Sound("./sfx/stomp.ogg")
        self.jump = mixer.Sound("./sfx/small_jump.ogg")
        self.death = mixer.Sound("./sfx/composiia-falha-critica-260131.mp3")
        self.kick = mixer.Sound("./sfx/kick.ogg")
        self.brick_bump = mixer.Sound("./sfx/brick-bump.ogg")
        self.powerup = mixer.Sound("./sfx/powerup.ogg")
        self.powerup_appear = mixer.Sound("./sfx/powerup_appears.ogg")
        self.pipe = mixer.Sound("./sfx/pipe.ogg")

        self.apply_volumes()

    # ---------- volumes ----------

    def apply_volumes(self) -> None:
        self.music_channel.set_volume(volume_to_gain(self.music_volume))
        self.sfx_channel.set_volume(volume_to_gain(self.sfx_volume))

    def set_music_volume(self, volume: int) -> None:
        self.music_volume = max(0, min(MAX_VOLUME, int(volume)))
        self.apply_volumes()

    def set_sfx_volume(self, volume: int) -> None:
        self.sfx_volume = max(0, min(MAX_VOLUME, int(volume)))
        self.apply_volumes()

    # ---------- musica ----------

    def play_music(self, sound=None, loops: int = -1,
                   fade_ms: int = MUSIC_FADE_IN_MS) -> None:
        if not self.music_on:
            return
        self.music_channel.play(sound or self.soundtrack, loops=loops,
                                fade_ms=fade_ms)

    def stop_music(self, fade_ms: int = MUSIC_FADE_OUT_MS) -> None:
        if fade_ms > 0:
            self.music_channel.fadeout(fade_ms)
        else:
            self.music_channel.stop()

    def music_playing(self) -> bool:
        return self.music_channel.get_busy()

    # ---------- sfx ----------

    def play_sfx(self, sfx) -> None:
        if self.allowSFX:
            self.sfx_channel.play(sfx)
