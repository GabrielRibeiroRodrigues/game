"""Persistencia: configuracoes (settings.json) e progresso (save/progress.json).

Gravacao atomica (arquivo temporario + os.replace) para nunca corromper o
save. Leituras toleram arquivo ausente/corrompido caindo nos defaults.
"""
import json
import os
import tempfile
from typing import Any, Dict

from core import config
from core.log import get_logger

log = get_logger(__name__)

PROGRESS_PATH = "./save/progress.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "sound": True,
    "sfx": True,
    "music_volume": 5,   # 0-10
    "sfx_volume": 5,     # 0-10
}
DEFAULT_PROGRESS: Dict[str, Any] = {
    "unlocked_phase": 0,   # maior indice de fase ja alcancado
    "best_score": 0,
}


def _load_json(path: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(defaults)
    try:
        with open(path) as fp:
            loaded = json.load(fp)
        if isinstance(loaded, dict):
            for key in defaults:
                if key in loaded:
                    data[key] = loaded[key]
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        log.warning("%s ilegivel (%s); usando defaults", path, exc)
    return data


def _save_json_atomic(path: str, data: Dict[str, Any]) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fp:
            json.dump(data, fp, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        log.error("falha ao salvar %s: %s", path, exc)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


class SaveManager:
    def __init__(self, settings_path: str = config.SETTINGS_PATH,
                 progress_path: str = PROGRESS_PATH) -> None:
        self.settings_path = settings_path
        self.progress_path = progress_path
        self.settings = _load_json(settings_path, DEFAULT_SETTINGS)
        self.progress = _load_json(progress_path, DEFAULT_PROGRESS)

    # ---------- settings ----------

    def save_settings(self) -> None:
        _save_json_atomic(self.settings_path, self.settings)

    # ---------- progresso ----------

    def record_phase_reached(self, phase_index: int) -> None:
        if phase_index > self.progress["unlocked_phase"]:
            self.progress["unlocked_phase"] = phase_index
            self._save_progress()

    def record_score(self, score: int) -> None:
        if score > self.progress["best_score"]:
            self.progress["best_score"] = score
            self._save_progress()

    def _save_progress(self) -> None:
        _save_json_atomic(self.progress_path, self.progress)
