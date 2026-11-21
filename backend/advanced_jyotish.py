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


def calculate_vimshottari(local_birth: datetime, moon_sidereal_longitude: float) -> dict:
    """Build the birth-started Mahadasha sequence; dates are approximate civil dates."""
    moon = norm(moon_sidereal_longitude)
    nak_index = min(26, int(moon / NAKSHATRA_SPAN))
    lord_index = nak_index % 9
    progress = (moon - nak_index * NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    first_lord = DASHA_LORDS[lord_index]
    first_balance = DASHA_YEARS[first_lord] * (1.0 - progress)
    cursor = local_birth
    periods = []
    for offset in range(9):
        lord = DASHA_LORDS[(lord_index + offset) % 9]
        years = first_balance if offset == 0 else float(DASHA_YEARS[lord])
        end = cursor + timedelta(days=years * YEAR_DAYS)
        periods.append({
            "lord": lord,
            "start": cursor.isoformat(),
            "end": end.isoformat(),
            "duration_years_approx": round(years, 4),
            "is_birth_balance": offset == 0,
        })
        cursor = end
    current = next((p for p in periods if datetime.fromisoformat(p["start"]) <= local_birth < datetime.fromisoformat(p["end"])), periods[0])
    return {
        "system": "Vimshottari Mahadasha",
        "birth_nakshatra": NAKSHATRAS[nak_index],
        "birth_nakshatra_lord": first_lord,
        "nakshatra_progress_fraction": round(progress, 6),
        "mahadasha_periods": periods,
        "birth_period": current["lord"],
        "calculation": "approximate_dates_from_low_precision_moon_longitude",
    }


def calculate_advanced_jyotish(local_birth: datetime, latitude: float, longitude: float) -> dict:
    """Return D9 placements and a birth-anchored Vimshottari sequence."""
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
        "vimshottari": calculate_vimshottari(local_birth, sidereal["Moon"]),
        "calculation": "advanced_derivations_from_low_precision_starter_ephemeris",
        "accuracy_note_hi": (
            "नवांश और विंशोत्तरी दशा की यह गणना प्रारंभिक निम्न-सटीकता ग्रह-स्थितियों पर आधारित है। "
            "जन्म समय, अयनांश और चन्द्र दीर्घांश की त्रुटि से परिणाम बदल सकते हैं। इसे भविष्यवाणी, "
            "विवाह/स्वास्थ्य/वित्त निर्णय या धार्मिक मुहूर्त के लिए प्रमाणित परिणाम न मानें; "
            "उच्च-सटीकता ephemeris और योग्य ज्योतिषाचार्य से सत्यापन आवश्यक है।"
        ),
    }
