from __future__ import annotations

import runpy
import sys
import types
from pathlib import Path


def _load_script():
    return runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts" / "download_ephemeris.py"),
        run_name="download_ephemeris_test",
    )


def test_ephemeris_downloader_uses_skyfield_loader_directory(monkeypatch, tmp_path):
    calls = {}
    skyfield = types.ModuleType("skyfield")
    api = types.ModuleType("skyfield.api")

    class FakeLoader:
        def __init__(self, directory):
            calls["directory"] = directory

        def __call__(self, filename):
            calls["filename"] = filename
            (Path(calls["directory"]) / filename).write_bytes(b"x" * 1_000_001)

    api.Loader = FakeLoader
    skyfield.api = api
    monkeypatch.setitem(sys.modules, "skyfield", skyfield)
    monkeypatch.setitem(sys.modules, "skyfield.api", api)
    monkeypatch.setattr(sys, "argv", ["download_ephemeris.py", "--directory", str(tmp_path)])

    assert _load_script()["main"]() == 0
    assert calls == {"directory": str(tmp_path.resolve()), "filename": "de440s.bsp"}
    assert (tmp_path / "de440s.bsp").stat().st_size == 1_000_001


def test_ephemeris_downloader_skips_valid_existing_file(monkeypatch, tmp_path):
    path = tmp_path / "de440s.bsp"
    path.write_bytes(b"x" * 1_000_000)
    monkeypatch.setattr(sys, "argv", ["download_ephemeris.py", "--directory", str(tmp_path)])
    assert _load_script()["main"]() == 0
