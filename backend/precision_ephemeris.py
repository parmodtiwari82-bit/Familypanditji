"""Optional JPL DE440s ephemeris adapter.

This supplies high-precision *tropical geocentric apparent* longitudes for the
Sun, Moon and visible planets. Sidereal conversion still uses the project's
approximate Lahiri ayanamsa; Rahu/Ketu are mean-node approximations. Therefore
this module is an astronomy upgrade component, not a certified Vedic engine.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
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


def calculate_sunrise_sunset(moment: datetime, latitude: float, longitude: float,
                             ephemeris_path: str | Path) -> dict[str, str | None]:
    """Find standard apparent sunrise/sunset events for the local civil day.

    Uses Skyfield's solar altitude convention (standard refraction + solar radius,
    approximately -0.833 degrees) with the local DE440s kernel. This is a geometric
    horizon calculation; terrain, buildings and local horizon obstructions are excluded.
    """
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("moment must be timezone-aware")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("latitude/longitude are outside valid ranges")
    if not EPHEMERIS_START_YEAR <= moment.year <= EPHEMERIS_END_YEAR:
        raise ValueError(
            f"DE440s supports dates from {EPHEMERIS_START_YEAR} through {EPHEMERIS_END_YEAR}"
        )
    path = Path(ephemeris_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"JPL ephemeris file not found: {path}")
    try:
        from skyfield.api import load, load_file, wgs84
        from skyfield import almanac
    except ImportError as exc:
        raise RuntimeError(
            "Optional astronomy dependencies are missing; install backend/requirements-astronomy.txt"
        ) from exc

    kernel = load_file(str(path))
    try:
        timescale = load.timescale(builtin=True)
        observer = wgs84.latlon(latitude_degrees=latitude, longitude_degrees=longitude)
        event_function = almanac.sunrise_sunset(kernel, observer)
        local_start = datetime.combine(moment.date(), datetime.min.time(), tzinfo=moment.tzinfo)
        local_end = local_start + timedelta(days=1)
        t0 = timescale.from_datetime(local_start.astimezone(timezone.utc))
        t1 = timescale.from_datetime(local_end.astimezone(timezone.utc))
        event_times, event_values = almanac.find_discrete(t0, t1, event_function)
        result: dict[str, str | None] = {"sunrise": None, "sunset": None}
        for event_time, is_sun_up in zip(event_times, event_values):
            key = "sunrise" if bool(is_sun_up) else "sunset"
            result[key] = event_time.utc_datetime().astimezone(moment.tzinfo).isoformat()
        return result
    finally:
        close = getattr(kernel, "close", None)
        if callable(close):
            close()
