"""
Vedic Astrology Calculation Engine
Powered by Swiss Ephemeris (pyswisseph), Lahiri ayanamsa.

Pure-functional and stateless: nothing here writes to disk or holds birth data
beyond the lifetime of the function call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import swisseph as swe

# ── Constants ─────────────────────────────────────────────────────────

PLANETS: dict[str, int | None] = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Ketu": None,  # derived as Rahu + 180
}

VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Moola",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishtha",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_TOTAL_YEARS = 120  # sum of all dasha years

TITHI_NAMES = [
    "Pratipada",
    "Dvitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dvadashi",
    "Trayodashi",
    "Chaturdashi",
    "Purnima",
    "Pratipada",
    "Dvitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dvadashi",
    "Trayodashi",
    "Chaturdashi",
    "Amavasya",
]
PAKSHA = ["Shukla"] * 15 + ["Krishna"] * 15

YOGA_NAMES = [
    "Vishkambha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shula",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyana",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
]

KARANA_NAMES = [
    "Bava",
    "Balava",
    "Kaulava",
    "Taitila",
    "Garaja",
    "Vanija",
    "Vishti",
    "Shakuni",
    "Chatushpada",
    "Naga",
    "Kimstughna",
]

VARA = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

LAGNA_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}


# ── Helpers ────────────────────────────────────────────────────────────


def _set_lahiri() -> None:
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def local_to_ut(
    year: int, month: int, day: int, hour: int, minute: int, tz_offset_hours: float
) -> float:
    """Convert local civil time + timezone offset to a Julian Day in UT."""
    ut_hour = hour + minute / 60.0 - tz_offset_hours
    return swe.julday(int(year), int(month), int(day), ut_hour)


def degrees_to_dms(deg: float) -> str:
    d = int(deg)
    m_full = (deg - d) * 60
    m = int(m_full)
    s = (m_full - m) * 60
    return f"{d}\u00b0{m:02d}'{s:04.1f}\""


def sign_info(lon: float) -> tuple[str, float, int]:
    lon = lon % 360
    idx = int(lon / 30)
    return SIGNS[idx], lon - idx * 30, idx


def nakshatra_info(lon: float) -> tuple[str, int, float, str]:
    lon = lon % 360
    span = 360.0 / 27
    idx = int(lon / span)
    deg_in = lon - idx * span
    pada = int(deg_in / (span / 4)) + 1
    return NAKSHATRAS[idx], pada, deg_in, NAKSHATRA_LORDS[idx]


def kp_sublord(lon: float) -> tuple[str, str, str]:
    """Return KP star lord, sub lord, sub-sub lord for a sidereal longitude."""
    lon = lon % 360
    nak_span = 360.0 / 27
    nak_idx = int(lon / nak_span)
    star_lord = NAKSHATRA_LORDS[nak_idx]
    deg_in_nak = lon - nak_idx * nak_span

    # Sub division: 9 sub-spans within the nakshatra, proportional to each lord's dasha years
    sub_start_idx = DASHA_ORDER.index(star_lord)
    sub_lord = star_lord
    sub_span_used = nak_span
    deg_in_sub = 0.0
    cumul = 0.0
    for i in range(9):
        li = (sub_start_idx + i) % 9
        lord_i = DASHA_ORDER[li]
        sub_span_i = (DASHA_YEARS[lord_i] / DASHA_TOTAL_YEARS) * nak_span
        if deg_in_nak <= cumul + sub_span_i:
            sub_lord = lord_i
            sub_span_used = sub_span_i
            deg_in_sub = deg_in_nak - cumul
            break
        cumul += sub_span_i

    # Sub-sub division: same logic, recursive within the sub span
    ss_start_idx = DASHA_ORDER.index(sub_lord)
    ss_lord = sub_lord
    cumul_ss = 0.0
    for j in range(9):
        ssi = (ss_start_idx + j) % 9
        ss = DASHA_ORDER[ssi]
        ss_span = (DASHA_YEARS[ss] / DASHA_TOTAL_YEARS) * sub_span_used
        if deg_in_sub <= cumul_ss + ss_span:
            ss_lord = ss
            break
        cumul_ss += ss_span

    return star_lord, sub_lord, ss_lord


def get_planet_lon(jd: float, pid: int) -> tuple[float, float]:
    _set_lahiri()
    r, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return r[0], r[3]


def get_ascendant(jd: float, lat: float, lon_geo: float) -> tuple[float, list[float]]:
    _set_lahiri()
    cusps, ascmc = swe.houses_ex(jd, lat, lon_geo, b"P", swe.FLG_SIDEREAL)
    return ascmc[0], list(cusps)


def get_ayanamsa(jd: float) -> float:
    _set_lahiri()
    return swe.get_ayanamsa_ut(jd)


def jd_to_date(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{int(d)} {months[m - 1]} {y}"


# ── Dasha Engine ──────────────────────────────────────────────────────


def vimshottari_dasha(moon_lon: float, birth_jd: float) -> list[tuple[str, float, float]]:
    """Return the full vimshottari mahadasha sequence as (lord, start_jd, end_jd)."""
    span = 360.0 / 27
    idx = int(moon_lon / span)
    deg_in = moon_lon - idx * span
    first_lord = NAKSHATRA_LORDS[idx]
    frac_rem = 1.0 - (deg_in / span)
    first_yrs = DASHA_YEARS[first_lord] * frac_rem
    dashas = []
    jd = birth_jd
    fidx = DASHA_ORDER.index(first_lord)
    for i in range(36):
        li = (fidx + i) % 9
        lord = DASHA_ORDER[li]
        yrs = first_yrs if i == 0 else DASHA_YEARS[lord]
        end = jd + yrs * 365.25
        dashas.append((lord, jd, end))
        jd = end
    return dashas


def antardasha_sequence(
    dashas: list[tuple[str, float, float]],
    from_jd: float,
    to_jd: float,
) -> list[tuple[str, str, float, float]]:
    """Every (mahadasha lord, antardasha lord, start_jd, end_jd) overlapping a window.

    Antardasha lengths follow the standard proportional rule: an antardasha
    runs for (maha years x antar years) / 120 years, starting from the
    mahadasha lord itself and proceeding in vimshottari order.
    """
    out: list[tuple[str, str, float, float]] = []
    for ml, ms, me in dashas:
        if me < from_jd or ms > to_jd:
            continue
        mi = DASHA_ORDER.index(ml)
        a_start = ms
        for i in range(9):
            al = DASHA_ORDER[(mi + i) % 9]
            a_yrs = (DASHA_YEARS[ml] * DASHA_YEARS[al]) / DASHA_TOTAL_YEARS
            a_end = a_start + a_yrs * 365.25
            if a_end >= from_jd and a_start <= to_jd:
                out.append((ml, al, a_start, a_end))
            a_start = a_end
    return out


def current_periods(
    dashas: list[tuple[str, float, float]],
    today_jd: float,
) -> tuple[tuple | None, tuple | None, tuple | None]:
    """Return (mahadasha, antardasha, pratyantar) entries active at today_jd."""
    maha = next(((lord, s, e) for lord, s, e in dashas if s <= today_jd < e), None)
    if not maha:
        return None, None, None
    ml, ms, _me = maha
    mi = DASHA_ORDER.index(ml)
    a_start = ms
    for i in range(9):
        al = DASHA_ORDER[(mi + i) % 9]
        a_yrs = (DASHA_YEARS[ml] * DASHA_YEARS[al]) / DASHA_TOTAL_YEARS
        a_end = a_start + a_yrs * 365.25
        if a_start <= today_jd < a_end:
            antar = (al, a_start, a_end)
            p_start = a_start
            ai = DASHA_ORDER.index(al)
            for j in range(9):
                pl = DASHA_ORDER[(ai + j) % 9]
                p_days = (
                    (DASHA_YEARS[ml] * DASHA_YEARS[al] * DASHA_YEARS[pl])
                    / (DASHA_TOTAL_YEARS * DASHA_TOTAL_YEARS)
                ) * 365.25
                p_end = p_start + p_days
                if p_start <= today_jd < p_end:
                    return maha, antar, (pl, p_start, p_end)
                p_start = p_end
        a_start = a_end
    return maha, None, None


# ── Panchanga ─────────────────────────────────────────────────────────


def get_tithi(sun_lon: float, moon_lon: float) -> tuple[str, str, float]:
    diff = (moon_lon - sun_lon) % 360
    idx = min(int(diff / 12), 29)
    return TITHI_NAMES[idx], PAKSHA[idx], diff


def get_yoga(sun_lon: float, moon_lon: float) -> str:
    return YOGA_NAMES[int(((sun_lon + moon_lon) % 360) / (360 / 27)) % 27]


def get_vara(jd: float) -> str:
    return VARA[int(jd + 1.5) % 7]


def get_karana(sun_lon: float, moon_lon: float) -> str:
    return KARANA_NAMES[int(((moon_lon - sun_lon) % 360) / 6) % 11]


# ── Chart Data Classes ────────────────────────────────────────────────


@dataclass
class Planet:
    name: str
    longitude: float
    sign: str
    sign_idx: int
    deg_in_sign: float
    nakshatra: str
    pada: int
    nak_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    house: int = 0
    retrograde: bool = False
    speed: float = 0.0


@dataclass
class Chart:
    label: str
    jd: float
    ayanamsa: float
    ascendant_lon: float
    ascendant_sign: str
    ascendant_sign_idx: int
    ascendant_deg: float
    ascendant_nak: str
    ascendant_pada: int
    ascendant_kp: tuple[str, str, str]
    planets: dict[str, Planet] = field(default_factory=dict)
    house_cusps: list[float] = field(default_factory=list)
    # Birth coordinates, kept so that strength and transit calculations that
    # need a place (dig bala, nathonnatha bala, sunrise) do not have to be
    # handed the location a second time. Never logged, never persisted.
    lat: float = 0.0
    lon_geo: float = 0.0
    tz: float = 0.0

    @property
    def local_hour(self) -> float:
        """Local civil hour of birth, 0-24, recovered from the Julian Day."""
        return (((self.jd + 0.5) % 1.0) * 24.0 + self.tz) % 24.0


def build_chart(
    label: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon_geo: float,
    tz: float = 5.5,
) -> Chart:
    """Build a sidereal natal/transit chart from civil time + place."""
    jd = local_to_ut(year, month, day, hour, minute, tz)
    ayanamsa = get_ayanamsa(jd)
    asc_lon, cusps = get_ascendant(jd, lat, lon_geo)
    asc_sign, asc_deg, asc_idx = sign_info(asc_lon)
    asc_nak, asc_pada, _, _ = nakshatra_info(asc_lon)
    asc_kp = kp_sublord(asc_lon)

    chart = Chart(
        label=label,
        jd=jd,
        ayanamsa=ayanamsa,
        ascendant_lon=asc_lon,
        ascendant_sign=asc_sign,
        ascendant_sign_idx=asc_idx,
        ascendant_deg=asc_deg,
        ascendant_nak=asc_nak,
        ascendant_pada=asc_pada,
        ascendant_kp=asc_kp,
        house_cusps=cusps,
        lat=lat,
        lon_geo=lon_geo,
        tz=tz,
    )

    for name, pid in PLANETS.items():
        if name == "Ketu" or pid is None:
            rahu = chart.planets["Rahu"]
            lon = (rahu.longitude + 180) % 360
            speed = -rahu.speed
        else:
            lon, speed = get_planet_lon(jd, pid)
        sign, deg, sidx = sign_info(lon)
        nak, pada, _, nak_lord = nakshatra_info(lon)
        sl, sub, ss = kp_sublord(lon)
        house = ((sidx - asc_idx) % 12) + 1
        retro = (speed < 0) and name not in ("Rahu", "Ketu")
        chart.planets[name] = Planet(
            name=name,
            longitude=lon,
            sign=sign,
            sign_idx=sidx,
            deg_in_sign=deg,
            nakshatra=nak,
            pada=pada,
            nak_lord=nak_lord,
            star_lord=sl,
            sub_lord=sub,
            sub_sub_lord=ss,
            house=house,
            retrograde=retro,
            speed=speed,
        )

    return chart


# ── Jaimini Karakas ────────────────────────────────────────────────────


def jaimini_karakas(chart: Chart) -> dict[str, str]:
    """Return the seven Jaimini chara karakas (Atmakaraka -> Darakaraka)."""
    core = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    ranked = sorted(core, key=lambda p: chart.planets[p].deg_in_sign, reverse=True)
    names = [
        "Atmakaraka",
        "Amatyakaraka",
        "Bhratrukaraka",
        "Matrukaraka",
        "Putrakaraka",
        "Gnatikaraka",
        "Darakaraka",
    ]
    return {names[i]: ranked[i] for i in range(7)}


# ── Navamsa (D9) ──────────────────────────────────────────────────────


def navamsa_sign_idx(longitude: float) -> int:
    """Return the navamsa (D9) sign index 0..11 for an absolute longitude.

    Standard Parashari rule: each sign is divided into 9 navamsas of 3°20'.
    The 1st navamsa of each sign starts from a fixed sign-index based on the
    element trine of the parent sign:
        fire trine  (Aries, Leo, Sagittarius)      -> Aries
        earth trine (Taurus, Virgo, Capricorn)     -> Capricorn
        air trine   (Gemini, Libra, Aquarius)      -> Libra
        water trine (Cancer, Scorpio, Pisces)      -> Cancer
    """
    longitude = longitude % 360.0
    sign_idx = int(longitude // 30)
    deg_in_sign = longitude - sign_idx * 30
    nav_within = int(deg_in_sign // (30.0 / 9.0))  # 0..8
    start = (12 - (sign_idx % 4) * 3) % 12
    return (start + nav_within) % 12


@dataclass
class NavamsaPosition:
    name: str
    sign: str
    house: int  # from natal D9 ascendant


def navamsa_chart(chart: Chart) -> dict[str, NavamsaPosition]:
    """Compute D9 placements for all bodies + derive D9 ascendant + houses."""
    asc_d9 = navamsa_sign_idx(chart.ascendant_lon)
    out: dict[str, NavamsaPosition] = {}
    for name in VEDIC_PLANETS:
        p = chart.planets[name]
        sidx = navamsa_sign_idx(p.longitude)
        house = ((sidx - asc_d9) % 12) + 1
        out[name] = NavamsaPosition(
            name=name,
            sign=SIGNS[sidx],
            house=house,
        )
    # store ascendant under a sentinel key
    out["__asc__"] = NavamsaPosition(
        name="Ascendant",
        sign=SIGNS[asc_d9],
        house=1,
    )
    return out


# ── Panchanga snapshot for a given chart ──────────────────────────────


@dataclass
class Panchanga:
    vara: str
    tithi: str
    paksha: str
    sun_moon_diff: float
    yoga: str
    karana: str
    moon_nakshatra: str
    moon_pada: int


def panchanga_for(chart: Chart) -> Panchanga:
    sun = chart.planets["Sun"]
    moon = chart.planets["Moon"]
    tithi, paksha, diff = get_tithi(sun.longitude, moon.longitude)
    return Panchanga(
        vara=get_vara(chart.jd),
        tithi=tithi,
        paksha=paksha,
        sun_moon_diff=diff,
        yoga=get_yoga(sun.longitude, moon.longitude),
        karana=get_karana(sun.longitude, moon.longitude),
        moon_nakshatra=moon.nakshatra,
        moon_pada=moon.pada,
    )
