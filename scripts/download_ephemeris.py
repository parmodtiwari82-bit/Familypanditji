#!/usr/bin/env python3
"""Download the official JPL DE440s ephemeris into a local data directory."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory",
        default="backend/data/ephemeris",
        help="destination directory (default: backend/data/ephemeris)",
    )
    args = parser.parse_args()
    destination = Path(args.directory).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    try:
        from skyfield.api import load
    except ImportError as exc:
        parser.error(
            "Skyfield is not installed. Run: pip install -r backend/requirements-astronomy.txt"
        )
        raise exc

    path = destination / "de440s.bsp"
    if path.exists():
        print(f"Already present: {path}")
        return 0
    # Skyfield downloads the official JPL DE440s file only when this command is run.
    load("de440s.bsp", directory=str(destination))
    if not path.is_file() or path.stat().st_size < 1_000_000:
        raise RuntimeError("DE440s download did not produce a valid local file")
    print(f"Downloaded DE440s: {path} ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
