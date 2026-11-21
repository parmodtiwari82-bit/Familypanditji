"""Advanced, explicitly approximate Jyotish derivations from the starter chart.

Navamsa and Vimshottari dates are mathematical derivations from the low-precision
Moon/planet positions in vedic_calc; they are not suitable for predictions or
ritual decisions until the underlying ephemeris is validated by qualified reviewers.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from math import floor

from vedic_calc import NAKSHATRAS, norm, nakshatra_name, tropical_longitudes, ayanamsa_lahiri_approx

DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
NAKSHATRA_SPAN = 360.0 / 27.0
NAVAMSA_SPAN = 30.0 / 9.0
DASHA_TOTAL = 120.0
YEAR_DAYS = 365.2425


def navamsa_sign(longitude: float) -> str:
    """Return D9 sign using classical movable/fixed/dual sign starting points."""
    from vedic_calc import SIGNS
    value = norm(longitude)
    rashi = int(value // 30)
    pada = min(8, int((value % 30) / NAVAMSA_SPAN))
    if rashi % 3 == 0:       # movable: begin from same sign
        start = rashi
    elif rashi % 3 == 1:     # fixed: begin from ninth sign
        start = (rashi + 8) % 12
    else:                   # dual: begin from fifth sign
        start = (rashi + 4) % 12
    return SIGNS[(start + pada) % 12]


def _period_record(lord: str, start: datetime, end: datetime, duration_years: float, birth: datetime) -> dict:
    return {
        "lord": lord,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "duration_years_approx": round(duration_years, 6),
        "active_at_birth": start <= birth < end,
    }


def _subperiods(start: datetime, parent_lord: str, parent_years: float,
                birth: datetime, depth: int) -> list[dict]:
    """Return mathematically proportional Antardasha (depth 1) or Pratyantardasha (depth 2)."""
    first_index = DASHA_LORDS.index(parent_lord)
    cursor = start
    result = []
    for offset in range(9):
        lord = DASHA_LORDS[(first_index + offset) % 9]
        years = parent_years * DASHA_YEARS[lord] / DASHA_TOTAL
        end = cursor + timedelta(days=years * YEAR_DAYS)
        item = _period_record(lord, cursor, end, years, birth)
        if depth == 1:
            item["pratyantardashas"] = _subperiods(cursor, lord, years, birth, 2)
        result.append(item)
        cursor = end
    return result


def calculate_vimshottari(local_birth: datetime, moon_sidereal_longitude: float) -> dict:
    """Build Mahadasha, Antardasha and Pratyantardasha dates from the birth Moon."""
    moon = norm(moon_sidereal_longitude)
    nak_index = min(26, int(moon / NAKSHATRA_SPAN))
    lord_index = nak_index % 9
    progress = (moon - nak_index * NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    first_lord = DASHA_LORDS[lord_index]
    first_balance = DASHA_YEARS[first_lord] * (1.0 - progress)
    elapsed_first_years = DASHA_YEARS[first_lord] - first_balance
    first_md_origin = local_birth - timedelta(days=elapsed_first_years * YEAR_DAYS)
    cursor = local_birth
    periods = []
    for offset in range(9):
        lord = DASHA_LORDS[(lord_index + offset) % 9]
        years = first_balance if offset == 0 else float(DASHA_YEARS[lord])
        md_origin = first_md_origin if offset == 0 else cursor
        md_end = cursor + timedelta(days=years * YEAR_DAYS)
        period = {
            "lord": lord,
            "start": cursor.isoformat(),
            "end": md_end.isoformat(),
            "duration_years_approx": round(years, 4),
            "is_birth_balance": offset == 0,
            "active_at_birth": cursor <= local_birth < md_end,
            "antardashas": _subperiods(md_origin, lord, float(DASHA_YEARS[lord]), local_birth, 1),
        }
        periods.append(period)
        cursor = md_end
    birth_md = next(p for p in periods if datetime.fromisoformat(p["start"]) <= local_birth < datetime.fromisoformat(p["end"]))
    birth_ad = next(a for a in birth_md["antardashas"] if datetime.fromisoformat(a["start"]) <= local_birth < datetime.fromisoformat(a["end"]))
    birth_pd = next(p for p in birth_ad["pratyantardashas"] if datetime.fromisoformat(p["start"]) <= local_birth < datetime.fromisoformat(p["end"]))
    return {
        "system": "Vimshottari Mahadasha / Antardasha / Pratyantardasha",
        "birth_nakshatra": NAKSHATRAS[nak_index],
        "birth_nakshatra_lord": first_lord,
        "nakshatra_progress_fraction": round(progress, 6),
        "mahadasha_periods": periods,
        "birth_period": birth_md["lord"],
        "birth_antardasha": birth_ad["lord"],
        "birth_pratyantardasha": birth_pd["lord"],
        "calculation": "approximate_dates_from_low_precision_moon_longitude",
    }


def divisional_sign(longitude: float, division: int, method: str) -> str:
    """Map a sidereal longitude to a classical varga sign for supported methods."""
    from vedic_calc import SIGNS
    if division < 1 or 360 % division != 0:
        raise ValueError("division must be a positive divisor of 360")
    value = norm(longitude)
    rashi = int(value // 30)
    part = min(division - 1, int((value % 30) / (30.0 / division)))
    if method == "hora":
        # Parashara Hora: odd signs alternate Leo/Cancer; even signs Cancer/Leo.
        target = (4 if part == 0 else 3) if rashi % 2 == 0 else (3 if part == 0 else 4)
    elif method == "drekkana":
        target = (rashi + (0, 4, 8)[part]) % 12
    elif method == "saptamsa":
        target = (rashi + part) % 12 if rashi % 2 == 0 else (rashi + 6 + part) % 12
    elif method == "dashamsa":
        target = (rashi + part) % 12 if rashi % 2 == 0 else (rashi + 8 + part) % 12
    elif method == "dwadasamsa":
        target = (rashi + part) % 12
    else:
        raise ValueError("unsupported varga method")
    return SIGNS[target]


def calculate_divisional_charts(sidereal: dict[str, float]) -> dict:
    """Calculate selected Parashari vargas from sidereal longitudes."""
    specs = {
        "d2_hora": (2, "hora"),
        "d3_drekkana": (3, "drekkana"),
        "d7_saptamsa": (7, "saptamsa"),
        "d10_dashamsa": (10, "dashamsa"),
        "d12_dwadasamsa": (12, "dwadasamsa"),
    }
    charts = {}
    for chart_id, (division, method) in specs.items():
        charts[chart_id] = {
            planet: {
                "rashi": divisional_sign(longitude, division, method),
                "source_longitude_degrees": round(norm(longitude), 4),
            }
            for planet, longitude in sidereal.items()
        }
    return charts


def calculate_advanced_jyotish(local_birth: datetime, latitude: float, longitude: float) -> dict:
    """Return selected varga charts and a birth-anchored Vimshottari sequence."""
    tropical = tropical_longitudes(local_birth)
    ayan = ayanamsa_lahiri_approx(local_birth)
    sidereal = {name: norm(value - ayan) for name, value in tropical.items()}
    navamsa = {
        name: {
            "longitude_degrees": round(value, 4),
            "rashi": navamsa_sign(value),
            "nakshatra": nakshatra_name(value),
        }
        for name, value in sidereal.items()
    }
    return {
        "birth_datetime_local": local_birth.isoformat(),
        "navamsa_d9": navamsa,
        "divisional_charts": calculate_divisional_charts(sidereal),
        "vimshottari": calculate_vimshottari(local_birth, sidereal["Moon"]),
        "calculation": "advanced_derivations_from_low_precision_starter_ephemeris",
        "accuracy_note_hi": (
            "नवांश और विंशोत्तरी दशा की यह गणना प्रारंभिक निम्न-सटीकता ग्रह-स्थितियों पर आधारित है। "
            "जन्म समय, अयनांश और चन्द्र दीर्घांश की त्रुटि से परिणाम बदल सकते हैं। इसे भविष्यवाणी, "
            "विवाह/स्वास्थ्य/वित्त निर्णय या धार्मिक मुहूर्त के लिए प्रमाणित परिणाम न मानें; "
            "उच्च-सटीकता ephemeris और योग्य ज्योतिषाचार्य से सत्यापन आवश्यक है।"
        ),
    }
