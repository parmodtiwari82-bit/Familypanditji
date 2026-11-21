"""Free, dependency-free approximate Vedic calendar and chart calculations.

Uses published low-precision orbital-element approximations (not a Swiss Ephemeris
replacement). Output is explicitly marked approximate and must be cross-checked
against a trusted regional Panchang/Acharya before ritual or life decisions.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from math import atan, atan2, cos, degrees, floor, radians, sin, sqrt, tan
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SIGNS = ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"]
NAKSHATRAS = ["अश्विनी","भरणी","कृत्तिका","रोहिणी","मृगशिरा","आर्द्रा","पुनर्वसु","पुष्य","आश्लेषा","मघा","पूर्वा फाल्गुनी","उत्तरा फाल्गुनी","हस्त","चित्रा","स्वाती","विशाखा","अनुराधा","ज्येष्ठा","मूल","पूर्वाषाढ़ा","उत्तराषाढ़ा","श्रवण","धनिष्ठा","शतभिषा","पूर्वा भाद्रपद","उत्तरा भाद्रपद","रेवती"]
TITHIS = ["शुक्ल प्रतिपदा","शुक्ल द्वितीया","शुक्ल तृतीया","शुक्ल चतुर्थी","शुक्ल पंचमी","शुक्ल षष्ठी","शुक्ल सप्तमी","शुक्ल अष्टमी","शुक्ल नवमी","शुक्ल दशमी","शुक्ल एकादशी","शुक्ल द्वादशी","शुक्ल त्रयोदशी","शुक्ल चतुर्दशी","पूर्णिमा","कृष्ण प्रतिपदा","कृष्ण द्वितीया","कृष्ण तृतीया","कृष्ण चतुर्थी","कृष्ण पंचमी","कृष्ण षष्ठी","कृष्ण सप्तमी","कृष्ण अष्टमी","कृष्ण नवमी","कृष्ण दशमी","कृष्ण एकादशी","कृष्ण द्वादशी","कृष्ण त्रयोदशी","कृष्ण चतुर्दशी","अमावस्या"]
YOGAS = ["विष्कम्भ","प्रीति","आयुष्मान","सौभाग्य","शोभन","अतिगण्ड","सुकर्मा","धृति","शूल","गण्ड","वृद्धि","ध्रुव","व्याघात","हर्षण","वज्र","सिद्धि","व्यतीपात","वरीयान","परिघ","शिव","सिद्ध","साध्य","शुभ","शुक्ल","ब्रह्म","इन्द्र","वैधृति"]
KARANAS = ["बव","बालव","कौलव","तैतिल","गर","वणिज","विष्टि","शकुनि","चतुष्पद","नाग","किंस्तुघ्न"]
PLANET_ELEMENTS = {
    "Mercury": (48.3313, 3.24587e-5, 7.0047, 5.00e-8, 29.1241, 1.01444e-5, .387098, 0, .205635, 5.59e-10, 168.6562, 4.0923344368),
    "Venus": (76.6799, 2.46590e-5, 3.3946, 2.75e-8, 54.8910, 1.38374e-5, .723330, 0, .006773, -1.302e-9, 48.0052, 1.6021302244),
    "Earth": (0, 0, 0, 0, 282.9404, 4.70935e-5, 1.0, 0, .016709, -1.151e-9, 356.0470, .9856002585),
    "Mars": (49.5574, 2.11081e-5, 1.8497, -1.78e-8, 286.5016, 2.92961e-5, 1.523688, 0, .093405, 2.516e-9, 18.6021, .5240207766),
    "Jupiter": (100.4542, 2.76854e-5, 1.3030, -1.557e-7, 273.8777, 1.64505e-5, 5.20256, 0, .048498, 4.469e-9, 19.8950, .0830853001),
    "Saturn": (113.6634, 2.38980e-5, 2.4886, -1.081e-7, 339.3939, 2.97661e-5, 9.55475, 0, .055546, -9.499e-9, 316.9670, .0334442282),
}
def norm(x: float) -> float:
    return x % 360.0

def jd(dt: datetime) -> float:
    utc = dt.astimezone(timezone.utc)
    return utc.timestamp() / 86400.0 + 2440587.5

def kepler_position(name: str, d: float) -> tuple[float, float, float]:
    N0, Nd, i0, id_, w0, wd, a0, ad, e0, ed, M0, Md = PLANET_ELEMENTS[name]
    N, inc, w = radians(N0 + Nd*d), radians(i0 + id_*d), radians(w0 + wd*d)
    a, e, M = a0 + ad*d, e0 + ed*d, radians(norm(M0 + Md*d))
    E = M + e*sin(M)*(1 + e*cos(M))
    for _ in range(8):
        E -= (E - e*sin(E) - M) / (1 - e*cos(E))
    xv, yv = a*(cos(E)-e), a*sqrt(1-e*e)*sin(E)
    v = atan2(yv, xv)
    r = sqrt(xv*xv + yv*yv)
    x = r*(cos(N)*cos(v+w)-sin(N)*sin(v+w)*cos(inc))
    y = r*(sin(N)*cos(v+w)+cos(N)*sin(v+w)*cos(inc))
    z = r*sin(v+w)*sin(inc)
    return x, y, z

def moon_longitude(d: float) -> float:
    N = radians(norm(125.1228 - .0529538083*d))
    inc = radians(5.1454)
    w = radians(norm(318.0634 + .1643573223*d))
    a, e = 60.2666, .0549
    M = radians(norm(115.3654 + 13.0649929509*d))
    E = M + e*sin(M)*(1+e*cos(M))
    for _ in range(8):
        E -= (E-e*sin(E)-M)/(1-e*cos(E))
    xv, yv = a*(cos(E)-e), a*sqrt(1-e*e)*sin(E)
    v, r = atan2(yv,xv), sqrt(xv*xv+yv*yv)
    x = r*(cos(N)*cos(v+w)-sin(N)*sin(v+w)*cos(inc))
    y = r*(sin(N)*cos(v+w)+cos(N)*sin(v+w)*cos(inc))
    lon = norm(degrees(atan2(y,x)))
    # Main lunar longitude perturbations (degrees).
    Ms = radians(norm(356.0470 + .9856002585*d))
    Lm = radians(norm(13.1763966*d + 218.316))
    D = radians(norm(297.8501921 + 12.19074912*d))
    F = radians(norm(93.2720950 + 13.22935024*d))
    lon += (-1.274*sin(M-2*D) + .658*sin(2*D) - .186*sin(Ms)
            - .059*sin(2*M-2*D) - .057*sin(M-2*D+Ms)
            + .053*sin(M+2*D) + .046*sin(2*D-Ms)
            + .041*sin(M-Ms) - .035*sin(D) - .031*sin(M+Ms)
            - .015*sin(2*F-2*D) + .011*sin(M-4*D))
    return norm(lon)

def tropical_longitudes(dt: datetime) -> dict[str, float]:
    d = jd(dt) - 2451543.5
    earth = kepler_position("Earth", d)
    result = {}
    for planet in ("Mercury","Venus","Mars","Jupiter","Saturn"):
        p = kepler_position(planet,d)
        result[planet] = norm(degrees(atan2(p[1]-earth[1],p[0]-earth[0])))
    result["Sun"] = norm(degrees(atan2(-earth[1],-earth[0])))
    result["Moon"] = moon_longitude(d)
    # Mean ascending lunar node (Rahu); Ketu is exactly opposite.
    result["Rahu"] = norm(125.04452 - 0.0529538083*d)
    result["Ketu"] = norm(result["Rahu"]+180)
    return result

def ayanamsa_lahiri_approx(dt: datetime) -> float:
    years = (jd(dt)-2451545.0)/365.2425
    return 23.85675 + years*(50.290966/3600)

def sign_name(lon: float) -> str:
    return SIGNS[int(norm(lon)//30)]

def nakshatra_name(lon: float) -> str:
    return NAKSHATRAS[int(norm(lon)/(360/27))]

def solar_event(day: date, latitude: float, longitude: float, sunrise: bool) -> str | None:
    # NOAA simplified sunrise/sunset calculation; UTC result converted by caller.
    n = day.timetuple().tm_yday
    lng_hour = longitude / 15
    t = n + ((6 if sunrise else 18) - lng_hour)/24
    M = .9856*t - 3.289
    L = norm(M + 1.916*sin(radians(M)) + .020*sin(2*radians(M)) + 282.634)
    RA = norm(degrees(atan(.91764*tan(radians(L)))))
    RA += floor(L/90)*90 - floor(RA/90)*90
    RA /= 15
    sin_dec = .39782*sin(radians(L))
    cos_dec = cos(asin_safe(sin_dec))
    cos_h = (cos(radians(90.833)) - sin_dec*sin(radians(latitude)))/(cos_dec*cos(radians(latitude)))
    if cos_h > 1 or cos_h < -1:
        return None
    H = (360-degrees(acos_safe(cos_h)) if sunrise else degrees(acos_safe(cos_h)))/15
    T = H + RA - .06571*t - 6.622
    utc_hours = (T - lng_hour) % 24
    utc_midnight = datetime.combine(day, time.min, tzinfo=timezone.utc)
    return (utc_midnight + timedelta(hours=utc_hours)).isoformat()

def asin_safe(x: float) -> float:
    from math import asin
    return asin(max(-1,min(1,x)))

def acos_safe(x: float) -> float:
    from math import acos
    return acos(max(-1,min(1,x)))

def _panchang_indices(moment: datetime, tropical_override: dict[str, float] | None = None) -> dict[str, int]:
    """Return the four moving Panchang limb indices at a timezone-aware instant."""
    longs = tropical_override or tropical_longitudes(moment)
    ayan = ayanamsa_lahiri_approx(moment)
    moon_sun = norm(longs["Moon"] - longs["Sun"])
    return {
        "tithi": min(29, int(moon_sun / 12.0)),
        "nakshatra": int(norm(longs["Moon"] - ayan) / (360.0 / 27.0)),
        "yoga": int(norm(longs["Sun"] + longs["Moon"] - 2.0 * ayan) / (360.0 / 27.0)),
        "karana": min(59, int(moon_sun / 6.0)),
    }


def _next_limb_transition(local_dt: datetime, limb: str) -> str | None:
    """Find the next approximate limb boundary using a coarse scan + binary search.

    This deliberately reports an estimate, not a certified Panchang transition.
    """
    initial = _panchang_indices(local_dt)[limb]
    left = local_dt
    right = local_dt + timedelta(hours=48)
    step = timedelta(minutes=10)
    probe = left + step
    found = None
    while probe <= right:
        if _panchang_indices(probe)[limb] != initial:
            found = probe
            break
        left = probe
        probe += step
    if found is None:
        return None
    right = found
    # Resolve the bracket to approximately one second.
    while (right - left).total_seconds() > 1:
        middle = left + (right - left) / 2
        if _panchang_indices(middle)[limb] == initial:
            left = middle
        else:
            right = middle
    return right.isoformat()


def calculate_panchang(local_dt: datetime, latitude: float, longitude: float,
                       tropical_override: dict[str, float] | None = None) -> dict:
    longs = tropical_override or tropical_longitudes(local_dt)
    moon_sun = norm(longs["Moon"]-longs["Sun"])
    tithi_index = min(29, int(moon_sun/12))
    yoga_index = int(norm(longs["Sun"]+longs["Moon"]-2*ayanamsa_lahiri_approx(local_dt))/(360/27))
    karana_index = int(moon_sun/6)
    if karana_index == 0:
        karana = "किंस्तुघ्न"
    elif karana_index >= 57:
        karana = ["शकुनि", "चतुष्पद", "नाग"][karana_index-57]
    else:
        karana = ["बव","बालव","कौलव","तैतिल","गर","वणिज","विष्टि"][(karana_index-1)%7]
    weekday = ["सोमवार","मंगलवार","बुधवार","गुरुवार","शुक्रवार","शनिवार","रविवार"][local_dt.weekday()]
    sunrise_utc = solar_event(local_dt.date(),latitude,longitude,True)
    sunset_utc = solar_event(local_dt.date(),latitude,longitude,False)
    tz = local_dt.tzinfo
    return {
        "date": local_dt.date().isoformat(), "weekday": weekday,
        "tithi": TITHIS[tithi_index], "tithi_number": tithi_index+1,
        "nakshatra": nakshatra_name(norm(longs["Moon"]-ayanamsa_lahiri_approx(local_dt))),
        "yoga": YOGAS[yoga_index], "karana": karana,
        "moon_sign": sign_name(norm(longs["Moon"]-ayanamsa_lahiri_approx(local_dt))),
        "sun_sign": sign_name(norm(longs["Sun"]-ayanamsa_lahiri_approx(local_dt))),
        "sunrise": datetime.fromisoformat(sunrise_utc).astimezone(tz).isoformat() if sunrise_utc else None,
        "sunset": datetime.fromisoformat(sunset_utc).astimezone(tz).isoformat() if sunset_utc else None,
        "limb_ends_at": ({
            "tithi": _next_limb_transition(local_dt, "tithi"),
            "nakshatra": _next_limb_transition(local_dt, "nakshatra"),
            "yoga": _next_limb_transition(local_dt, "yoga"),
            "karana": _next_limb_transition(local_dt, "karana"),
        } if tropical_override is None else None),
        "transition_times_status": ("estimated_low_precision" if tropical_override is None else "not_calculated_for_jpl_mode"),
        "calculation": ("free_low_precision_astronomical_approximation" if tropical_override is None else "jpl_de440s_planetary_positions_with_approximate_vedic_conventions"),
        "accuracy_note_hi": "यह निःशुल्क प्रारंभिक खगोलीय गणना है। स्थानीय पंचांग, अयनांश, दृश्य क्षितिज और परंपरा के अनुसार अंतर हो सकता है। पूजा/व्रत के अंतिम निर्णय से पहले स्थानीय प्रमाणित पंचांग/आचार्य से मिलान करें।",
    }

def calculate_kundli(local_dt: datetime, latitude: float, longitude: float,
                     tropical_override: dict[str, float] | None = None) -> dict:
    longs = tropical_override or tropical_longitudes(local_dt)
    ayan = ayanamsa_lahiri_approx(local_dt)
    sidereal = {name: norm(value-ayan) for name,value in longs.items()}
    # Approximate local sidereal time and ascendant from ecliptic horizon intersection.
    utc = local_dt.astimezone(timezone.utc)
    T = (jd(utc)-2451545.0)/36525
    gmst = norm(280.46061837 + 360.98564736629*(jd(utc)-2451545.0) + .000387933*T*T - T*T*T/38710000)
    lst = radians(norm(gmst+longitude))
    eps = radians(23.439291 - .0130042*T)
    lat = radians(latitude)
    asc = norm(degrees(atan2(-cos(lst), sin(lst)*cos(eps)+tan(lat)*sin(eps))))
    asc_sidereal = norm(asc-ayan)
    planets = {name: {"longitude_degrees": round(value,4), "rashi": sign_name(value), "nakshatra": nakshatra_name(value)} for name,value in sidereal.items()}
    return {
        "birth_datetime_local": local_dt.isoformat(), "latitude": latitude, "longitude": longitude,
        "ayanamsa": "Lahiri-style approximate", "ayanamsa_degrees": round(ayan,5),
        "lagna": {"longitude_degrees": round(asc_sidereal,4), "rashi": sign_name(asc_sidereal)},
        "planets": planets,
        "house_system": "whole_sign_from_approximate_ascendant",
        "calculation": "free_low_precision_orbital_approximation",
        "accuracy_note_hi": "यह निःशुल्क प्रारंभिक जन्मकुंडली गणना है, प्रमाणित ज्योतिषीय पंचांग/Swiss Ephemeris स्तर की सटीकता का दावा नहीं। जन्म समय में कुछ मिनट का अंतर लग्न बदल सकता है। दशा, वर्ग कुंडली, वक्री/अस्त स्थिति और मुहूर्त के लिए अलग सत्यापित गणना व आचार्य समीक्षा आवश्यक है।",
    }

def parse_local_datetime(day: str, clock: str, timezone_name: str) -> datetime:
    try:
        zone = ZoneInfo(timezone_name)
        parsed_day = date.fromisoformat(day)
        parsed_time = time.fromisoformat(clock)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ValueError("Use valid ISO date, local time and IANA timezone (e.g. Asia/Kolkata).") from exc
    return datetime.combine(parsed_day, parsed_time, tzinfo=zone)
