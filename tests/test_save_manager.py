import json
import os

from core.save import SaveManager, DEFAULT_SETTINGS, DEFAULT_PROGRESS


def make(tmp_path):
    return SaveManager(
        settings_path=str(tmp_path / "settings.json"),
        progress_path=str(tmp_path / "save" / "progress.json"),
    )


def test_defaults_when_files_missing(tmp_path):
    sm = make(tmp_path)
    assert sm.settings == DEFAULT_SETTINGS
    assert sm.progress == DEFAULT_PROGRESS


def test_settings_roundtrip(tmp_path):
    sm = make(tmp_path)
    sm.settings["music_volume"] = 8
    sm.settings["sound"] = False
    sm.save_settings()
    sm2 = make(tmp_path)
    assert sm2.settings["music_volume"] == 8
    assert sm2.settings["sound"] is False


def test_progress_only_advances(tmp_path):
    sm = make(tmp_path)
    sm.record_phase_reached(2)
    sm.record_phase_reached(1)  # nao regride
    assert sm.progress["unlocked_phase"] == 2
    sm2 = make(tmp_path)
    assert sm2.progress["unlocked_phase"] == 2


def test_best_score_keeps_maximum(tmp_path):
    sm = make(tmp_path)
    sm.record_score(500)
    sm.record_score(300)
    assert sm.progress["best_score"] == 500
    assert make(tmp_path).progress["best_score"] == 500


def test_corrupted_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{nao é json")
    sm = make(tmp_path)
    assert sm.settings == DEFAULT_SETTINGS


def test_partial_file_merges_with_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"sfx": False}))
    sm = make(tmp_path)
    assert sm.settings["sfx"] is False
    assert sm.settings["music_volume"] == DEFAULT_SETTINGS["music_volume"]


def test_atomic_write_leaves_no_tmp_files(tmp_path):
    sm = make(tmp_path)
    sm.record_score(100)
    save_dir = tmp_path / "save"
    leftovers = [f for f in os.listdir(save_dir) if f.endswith(".tmp")]
    assert leftovers == []
