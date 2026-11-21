"""Optional JPL DE440s ephemeris adapter.

This supplies high-precision *tropical geocentric apparent* longitudes for the
Sun, Moon and visible planets. Sidereal conversion still uses the project's
approximate Lahiri ayanamsa; Rahu/Ketu are mean-node approximations. Therefore
this module is an astronomy upgrade component, not a certified Vedic engine.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vedic_calc import ayanamsa_lahiri_approx, jd, norm

EPHEMERIS_START_YEAR = 1849
EPHEMERIS_END_YEAR = 2150
BODY_KEYS = {
    "Sun": "sun",
    "Moon": "moon",
    "Mercury": "mercury",
    "Venus": "venus",
    "Mars": "mars",
    "Jupiter": "jupiter barycenter",
    "Saturn": "saturn barycenter",
}


def mean_node_longitudes(moment: datetime) -> tuple[float, float]:
    """Return approximate mean Rahu and opposite Ketu longitudes."""
    days_since_j2000 = jd(moment) - 2451545.0
    rahu = norm(125.04452 - 0.0529538083 * days_since_j2000)
    return rahu, norm(rahu + 180.0)


def to_sidereal_longitudes(tropical: dict[str, float], moment: datetime) -> dict[str, float]:
    """Apply the existing approximate Lahiri ayanamsa consistently to all bodies."""
    ayanamsa = ayanamsa_lahiri_approx(moment)
    result = {name: norm(value - ayanamsa) for name, value in tropical.items()}
    rahu, ketu = mean_node_longitudes(moment)
    result["Rahu"] = norm(rahu - ayanamsa)
    result["Ketu"] = norm(ketu - ayanamsa)
    return result


def calculate_tropical_longitudes(moment: datetime, ephemeris_path: str | Path) -> dict:
    """Calculate geocentric apparent ecliptic longitudes using a local DE440s file.

    Skyfield is an optional dependency. The ephemeris file is never downloaded
    implicitly by this function; install it explicitly with scripts/download_ephemeris.py.
    """
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("moment must be timezone-aware")
    if not EPHEMERIS_START_YEAR <= moment.year <= EPHEMERIS_END_YEAR:
        raise ValueError(
            f"DE440s supports dates from {EPHEMERIS_START_YEAR} through {EPHEMERIS_END_YEAR}"
        )
    path = Path(ephemeris_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"JPL ephemeris file not found: {path}")

    try:
        from skyfield.api import load, load_file
        from skyfield.framelib import ecliptic_frame
    except ImportError as exc:
        raise RuntimeError(
            "Optional astronomy dependencies are missing; install backend/requirements-astronomy.txt"
        ) from exc

    kernel = load_file(str(path))
    try:
        timescale = load.timescale(builtin=True)
        instant = timescale.from_datetime(moment.astimezone(timezone.utc))
        earth = kernel["earth"]
        positions = {}
        for display_name, body_name in BODY_KEYS.items():
            apparent = earth.at(instant).observe(kernel[body_name]).apparent()
            _latitude, longitude, _distance = apparent.frame_latlon(ecliptic_frame)
            positions[display_name] = norm(float(longitude.degrees))
        return positions
    finally:
        close = getattr(kernel, "close", None)
        if callable(close):
            close()
