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


def calculate_panchang_limb_transitions(moment: datetime, ephemeris_path: str | Path,
                                        max_hours: int = 48) -> dict[str, str | None]:
    """Find next Panchang limb boundaries using one local DE440s kernel session.

    Planetary positions come from JPL DE440s. Sidereal nakshatra/yoga boundaries
    still depend on the project's approximate Lahiri ayanamsa; this is not a
    tradition-certified Panchang. A 10-minute scan brackets each boundary and a
    binary search resolves the crossing to about one second.
    """
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("moment must be timezone-aware")
    if not EPHEMERIS_START_YEAR <= moment.year <= EPHEMERIS_END_YEAR:
        raise ValueError(
            f"DE440s supports dates from {EPHEMERIS_START_YEAR} through {EPHEMERIS_END_YEAR}"
        )
    if not 1 <= max_hours <= 96:
        raise ValueError("max_hours must be between 1 and 96")
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

    def limb_indices(instant, earth, kernel):
        apparent_sun = earth.at(instant).observe(kernel["sun"]).apparent()
        apparent_moon = earth.at(instant).observe(kernel["moon"]).apparent()
        _sun_lat, sun_lon, _sun_distance = apparent_sun.frame_latlon(ecliptic_frame)
        _moon_lat, moon_lon, _moon_distance = apparent_moon.frame_latlon(ecliptic_frame)
        tropical_sun = norm(float(sun_lon.degrees))
        tropical_moon = norm(float(moon_lon.degrees))
        local_dt = instant.utc_datetime().astimezone(moment.tzinfo)
        ayan = ayanamsa_lahiri_approx(local_dt)
        separation = norm(tropical_moon - tropical_sun)
        return {
            "tithi": min(29, int(separation / 12.0)),
            "nakshatra": int(norm(tropical_moon - ayan) / (360.0 / 27.0)),
            "yoga": int(norm(tropical_sun + tropical_moon - 2.0 * ayan) / (360.0 / 27.0)),
            "karana": min(59, int(separation / 6.0)),
        }

    kernel = load_file(str(path))
    try:
        timescale = load.timescale(builtin=True)
        earth = kernel["earth"]
        start_utc = moment.astimezone(timezone.utc)
        end_utc = start_utc + timedelta(hours=max_hours)
        start_t = timescale.from_datetime(start_utc)
        end_t = timescale.from_datetime(end_utc)
        initial = limb_indices(start_t, earth, kernel)
        found: dict[str, datetime] = {}
        previous_dt = start_utc
        previous_t = start_t
        step = timedelta(minutes=10)
        probe_dt = previous_dt + step
        while probe_dt <= end_utc and len(found) < 4:
            probe_t = timescale.from_datetime(probe_dt)
            indices = limb_indices(probe_t, earth, kernel)
            for limb in ("tithi", "nakshatra", "yoga", "karana"):
                if limb in found or indices[limb] == initial[limb]:
                    continue
                left_dt, right_dt = previous_dt, probe_dt
                left_t = previous_t
                while (right_dt - left_dt).total_seconds() > 1:
                    middle_dt = left_dt + (right_dt - left_dt) / 2
                    middle_t = timescale.from_datetime(middle_dt)
                    if limb_indices(middle_t, earth, kernel)[limb] == initial[limb]:
                        left_dt, left_t = middle_dt, middle_t
                    else:
                        right_dt = middle_dt
                found[limb] = right_dt.astimezone(moment.tzinfo)
            previous_dt, previous_t = probe_dt, probe_t
            probe_dt += step
        return {limb: found[limb].isoformat() if limb in found else None
                for limb in ("tithi", "nakshatra", "yoga", "karana")}
    finally:
        close = getattr(kernel, "close", None)
        if callable(close):
            close()


def calculate_tropical_ascendant(moment: datetime, latitude: float, longitude: float,
                                 ephemeris_path: str | Path) -> float:
    """Calculate tropical ascendant using Skyfield apparent Greenwich sidereal time.

    The sidereal-time angle is taken from Skyfield's time scale. Obliquity of date
    still uses the project's compact polynomial approximation, so this is an
    improved ascendant input, not a certified high-precision house calculation.
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
        from skyfield.api import load, load_file
    except ImportError as exc:
        raise RuntimeError(
            "Optional astronomy dependencies are missing; install backend/requirements-astronomy.txt"
        ) from exc

    kernel = load_file(str(path))
    try:
        timescale = load.timescale(builtin=True)
        instant = timescale.from_datetime(moment.astimezone(timezone.utc))
        local_sidereal_degrees = norm(float(instant.gast) * 15.0 + longitude)
        centuries = (jd(moment) - 2451545.0) / 36525.0
        obliquity = radians(23.439291 - 0.0130042 * centuries)
        local_sidereal = radians(local_sidereal_degrees)
        geographic_latitude = radians(latitude)
        ascendant = degrees(__import__("math").atan2(
            -__import__("math").cos(local_sidereal),
            __import__("math").sin(local_sidereal) * __import__("math").cos(obliquity)
            + __import__("math").tan(geographic_latitude) * __import__("math").sin(obliquity),
        ))
        return norm(ascendant)
    finally:
        close = getattr(kernel, "close", None)
        if callable(close):
            close()
