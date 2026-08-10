"""
ReportLab-based PDF generator for the KOSMA Soul Blueprint.

Streams to a BytesIO buffer; never touches the filesystem and never logs
birth data.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

from reportlab.graphics.shapes import (
    Circle,
    Drawing,
    Line,
    String,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import ashtakavarga as av
from . import evidence as ev
from . import interpretations as interp
from . import numerology as numero
from . import placements as plc
from . import shadbala as sb
from . import transits as tr
from . import vedic_engine as ve
from . import yogas as yg
from .vedic_engine import Chart, Panchanga

# ── Planet symbols, and the refusal to print a box ────────────────────
#
# ReportLab's built-in Helvetica is Type 1 with WinAnsi encoding, and none of
# U+2609..U+264F is in it. Asking for ☉ does not fail -- it silently draws
# the notdef glyph, so every planet in the report comes out as an identical
# black box. That was the state of this file: symbols requested, boxes
# delivered.
#
# So a TrueType face carrying the glyphs is registered when one can be found,
# and *the symbol is only ever emitted if the font really has it*. Where it
# does not, the two-letter abbreviation is used instead. A reader may see "Sa"
# rather than ♄ on a machine with no suitable font, which is a small loss; a
# reader must never see ■, which is a defect.

SYMBOLS: dict[str, str] = {
    "Sun": "\u2609",
    "Moon": "\u263d",
    "Mars": "\u2642",
    "Mercury": "\u263f",
    "Jupiter": "\u2643",
    "Venus": "\u2640",
    "Saturn": "\u2644",
    "Rahu": "\u260a",
    "Ketu": "\u260b",
}

ABBREV: dict[str, str] = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

# Debian ships DejaVu in fonts-dejavu-core, which the Dockerfile installs;
# Segoe UI Symbol covers Windows; the rest are common fallbacks. First hit
# wins, and none being present is a supported outcome.
_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:\\Windows\\Fonts\\seguisym.ttf",
    "C:\\Windows\\Fonts\\arialuni.ttf",
)

SYMBOL_FONT: str | None = None
SYMBOL_OK: frozenset[str] = frozenset()


def _register_symbol_font() -> tuple[str | None, frozenset[str]]:
    """Find a face carrying the graha glyphs, and record which it actually has.

    Coverage is checked per glyph against the font's own character map, not by
    comparing widths. Width comparison was the first attempt and it is not
    sound: a face carrying seven of the nine still produces several distinct
    widths, passes the check, and then draws a box for the two it lacks. The
    lunar nodes are exactly the two most fonts are missing, so that is the
    common case rather than a corner one.

    Partial coverage is therefore honoured per planet: whatever the font has
    is drawn as a symbol, and the rest fall back to the abbreviation.
    """
    import os

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for path in _FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        name = "KosmaSymbols"
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            char_map = getattr(pdfmetrics.getFont(name).face, "charToGlyph", None)
            if not char_map:
                continue
            covered = frozenset(planet for planet, sym in SYMBOLS.items() if ord(sym) in char_map)
            if covered:
                return name, covered
        except Exception:
            continue
    return None, frozenset()


SYMBOL_FONT, SYMBOL_OK = _register_symbol_font()


def _sigil(planet: str) -> str:
    """The symbol where it will render, the abbreviation where it will not."""
    if SYMBOL_FONT and planet in SYMBOL_OK:
        return f'<font face="{SYMBOL_FONT}">{SYMBOLS[planet]}</font>'
    return ABBREV[planet]


# ── Colour palette ────────────────────────────────────────────────────

INK = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#7c3aed")
MUTED = colors.HexColor("#6b7280")
GOLD = colors.HexColor("#b08d57")
LINE = colors.HexColor("#d1d5db")
BG_ALT = colors.HexColor("#f5f3ff")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "wordmark": ParagraphStyle(
            "wordmark",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=42,
            leading=46,
            textColor=ACCENT,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="Helvetica",
            fontSize=20,
            leading=24,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=11,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=MUTED,
            alignment=TA_LEFT,
        ),
        "label": ParagraphStyle(
            "label",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=GOLD,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }


# ── Helpers ───────────────────────────────────────────────────────────


def _pct(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(100.0, (x - lo) / (hi - lo) * 100.0))


def _month_name(m: int) -> str:
    return [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ][m]


def _retro(p) -> str:
    return " R" if p.retrograde else ""


# ── Chart wheel (circular sidereal chart) ────────────────────────────

PLANET_GLYPH = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

SIGN_ABBR = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]


def _wheel_xy(cx: float, cy: float, longitude: float, radius: float) -> tuple[float, float]:
    """Map a sidereal longitude to (x, y) on the wheel.

    Convention: 0 deg Aries at top (12 o'clock), longitude increases clockwise.
    """
    import math

    angle_rad = math.radians(90.0 - longitude)
    return cx + radius * math.cos(angle_rad), cy + radius * math.sin(angle_rad)


def _chart_wheel(natal, size_cm: float = 11.0) -> Drawing:
    """Render a circular sidereal chart wheel as a ReportLab Drawing.

    Outer ring: 12 sign sectors (30 deg each).
    Middle band: house numbers 1..12 starting from the natal ascendant.
    Inner positions: planet glyphs at exact sidereal longitude.
    Lagna marker: a bold accent line from center to the ascendant longitude.
    """

    side = size_cm * cm
    d = Drawing(side, side)
    cx = cy = side / 2

    r_outer = side * 0.46
    r_band = side * 0.36
    r_inner = side * 0.28
    r_planets = side * 0.22

    # Background discs
    d.add(Circle(cx, cy, r_outer, fillColor=colors.white, strokeColor=ACCENT, strokeWidth=1.2))
    d.add(Circle(cx, cy, r_band, fillColor=BG_ALT, strokeColor=LINE, strokeWidth=0.4))
    d.add(Circle(cx, cy, r_inner, fillColor=colors.white, strokeColor=LINE, strokeWidth=0.4))

    # Sign dividers + labels
    for i in range(12):
        lon = i * 30.0
        # divider line outer to inner
        x1, y1 = _wheel_xy(cx, cy, lon, r_outer)
        x2, y2 = _wheel_xy(cx, cy, lon, r_inner)
        d.add(Line(x1, y1, x2, y2, strokeColor=LINE, strokeWidth=0.3))
        # sign abbreviation, midpoint of the sector
        mid_lon = lon + 15.0
        lx, ly = _wheel_xy(cx, cy, mid_lon, (r_outer + r_band) / 2)
        s = String(
            lx,
            ly - 3,
            SIGN_ABBR[i],
            fontName="Helvetica-Bold",
            fontSize=8,
            fillColor=GOLD,
            textAnchor="middle",
        )
        d.add(s)

    # House numbers (whole-sign houses from the natal ascendant)
    asc_idx = natal.ascendant_sign_idx
    for h in range(1, 13):
        sign_idx = (asc_idx + h - 1) % 12
        mid_lon = sign_idx * 30 + 15
        hx, hy = _wheel_xy(cx, cy, mid_lon, (r_band + r_inner) / 2)
        d.add(
            String(
                hx,
                hy - 3,
                str(h),
                fontName="Helvetica-Bold",
                fontSize=9,
                fillColor=ACCENT,
                textAnchor="middle",
            )
        )

    # Lagna (ascendant) marker line
    asc_x, asc_y = _wheel_xy(cx, cy, natal.ascendant_lon, r_outer + 4)
    cx_inner, cy_inner = _wheel_xy(cx, cy, natal.ascendant_lon, r_inner)
    d.add(Line(cx_inner, cy_inner, asc_x, asc_y, strokeColor=ACCENT, strokeWidth=1.6))
    # ASC label just outside the wheel
    label_x, label_y = _wheel_xy(cx, cy, natal.ascendant_lon, r_outer + 16)
    d.add(
        String(
            label_x,
            label_y - 3,
            "ASC",
            fontName="Helvetica-Bold",
            fontSize=8,
            fillColor=ACCENT,
            textAnchor="middle",
        )
    )

    # Planets — to keep glyphs from overlapping when several share a sign,
    # group planets into 5 deg buckets and stagger radius slightly.
    from collections import defaultdict

    buckets: dict[int, list] = defaultdict(list)
    for name, p in natal.planets.items():
        if name not in PLANET_GLYPH:
            continue
        buckets[int(p.longitude // 5)].append((name, p))

    for bucket in buckets.values():
        for k, (name, p) in enumerate(bucket):
            offset = (k - (len(bucket) - 1) / 2.0) * 7
            r = r_planets + offset
            px, py = _wheel_xy(cx, cy, p.longitude, r)
            glyph = PLANET_GLYPH[name]
            if p.retrograde:
                # Plain "R". This was U+2832, a braille pattern chosen as a
                # "tiny mark", which Helvetica has no glyph for -- so every
                # retrograde planet on the wheel drew a black box instead.
                glyph += "R"
            d.add(
                String(
                    px,
                    py - 3,
                    glyph,
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    fillColor=INK,
                    textAnchor="middle",
                )
            )

    # Centre wordmark
    d.add(
        String(
            cx,
            cy + 3,
            "KOSMA",
            fontName="Helvetica-Bold",
            fontSize=11,
            fillColor=ACCENT,
            textAnchor="middle",
        )
    )
    d.add(
        String(
            cx,
            cy - 9,
            natal.ascendant_sign,
            fontName="Helvetica",
            fontSize=7,
            fillColor=MUTED,
            textAnchor="middle",
        )
    )

    return d


def _wheel_section(natal, styles: dict) -> list:
    return [
        Paragraph("Birth Chart Wheel", styles["h1"]),
        Paragraph(
            "Sidereal positions on a 12-sign wheel. The accent line marks the "
            "ascendant. Numbers 1\u201312 trace whole-sign houses from the lagna. "
            "Sign abbreviations sit on the outer band.",
            styles["muted"],
        ),
        Spacer(1, 4),
        _chart_wheel(natal),
    ]


# ── D9 Navamsa table ─────────────────────────────────────────────────


def _navamsa_table(natal, styles: dict) -> list:
    nav = ve.navamsa_chart(natal)
    asc = nav["__asc__"]
    rows = [["Body", "D9 Sign", "D9 House (from D9 asc)"]]
    rows.append(["Ascendant", asc.sign, "1"])
    for name in ve.VEDIC_PLANETS:
        np_ = nav[name]
        rows.append([name, np_.sign, str(np_.house)])
    t = Table(rows, colWidths=[3.4 * cm, 5.2 * cm, 5.2 * cm], repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GOLD),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.25, LINE),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ]
        )
    )
    return [
        Paragraph("D9 Navamsa", styles["h1"]),
        Paragraph(
            "The Navamsa or D9 chart, considered the inner half of the natal "
            "chart in Vedic astrology, is read for marriage, dharma, and "
            "the strength of planets in their soul-truth. A planet that "
            "shifts to a friendly sign in D9 is said to gain inner power.",
            styles["muted"],
        ),
        Spacer(1, 6),
        t,
    ]


# ── Section builders ──────────────────────────────────────────────────


def _cover(
    name: str, dob: tuple[int, int, int], tob: tuple[int, int], place: str, styles: dict
) -> list:
    y, m, d = dob
    h, mn = tob
    when = f"{d} {_month_name(m)} {y} \u00b7 {h:02d}:{mn:02d}"
    return [
        Spacer(1, 3.5 * cm),
        Paragraph("KOSMA", styles["wordmark"]),
        Paragraph("Soul Blueprint", styles["title"]),
        Paragraph("Your sky, your story, in five letters.", styles["subtitle"]),
        Spacer(1, 1.2 * cm),
        HRFlowable(
            width="60%", thickness=0.6, color=GOLD, hAlign="CENTER", spaceBefore=4, spaceAfter=18
        ),
        Paragraph(f"<b>{_esc(name) or 'Anonymous Soul'}</b>", styles["h1"]),
        Paragraph(when, styles["body"]),
        Paragraph(_esc(place), styles["body"]),
        Spacer(1, 1.2 * cm),
        HRFlowable(
            width="60%", thickness=0.4, color=LINE, hAlign="CENTER", spaceBefore=4, spaceAfter=14
        ),
        Paragraph(
            "Lahiri ayanamsa \u00b7 sidereal positions \u00b7 KP star/sub/sub-sub "
            "lord chains \u00b7 Vimshottari dasha \u00b7 Jaimini karakas",
            styles["muted"],
        ),
        PageBreak(),
    ]


def _birth_summary(natal: Chart, place: str, styles: dict) -> list:
    asc_dms = ve.degrees_to_dms(natal.ascendant_deg)
    asc_kp = "/".join(natal.ascendant_kp)
    lord = ve.LAGNA_LORDS[natal.ascendant_sign]
    rows = [
        [
            "Ascendant",
            f"{natal.ascendant_sign} {asc_dms} \u00b7 "
            f"{natal.ascendant_nak} pada {natal.ascendant_pada}",
        ],
        ["KP chain (asc)", asc_kp],
        ["Lagna lord", lord],
        ["Ayanamsa (Lahiri)", f"{natal.ayanamsa:.4f}\u00b0"],
        ["Place of birth", place],
    ]
    t = Table(rows, colWidths=[4.2 * cm, 12 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                ("TEXTCOLOR", (0, 0), (0, -1), GOLD),
                ("TEXTCOLOR", (1, 0), (1, -1), INK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE),
            ]
        )
    )
    return [
        Paragraph("Birth Snapshot", styles["h1"]),
        t,
        Spacer(1, 6),
    ]


def _planet_table(natal: Chart, styles: dict) -> list:
    header = ["Planet", "Sign", "Degree", "Nakshatra (Pada)", "KP Star/Sub/SS", "House"]
    rows = [header]
    for name in ve.VEDIC_PLANETS:
        p = natal.planets[name]
        rows.append(
            [
                name + _retro(p),
                p.sign,
                ve.degrees_to_dms(p.deg_in_sign),
                f"{p.nakshatra} ({p.pada})",
                f"{p.star_lord}/{p.sub_lord}/{p.sub_sub_lord}",
                str(p.house),
            ]
        )
    t = Table(
        rows, colWidths=[2.4 * cm, 2.6 * cm, 2.6 * cm, 4.2 * cm, 4.0 * cm, 1.4 * cm], repeatRows=1
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
                ("ALIGN", (5, 0), (5, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, ACCENT),
                ("BOX", (0, 0), (-1, -1), 0.25, LINE),
            ]
        )
    )
    return [
        Paragraph("Planetary Positions", styles["h1"]),
        Paragraph(
            "Sidereal longitudes from Swiss Ephemeris, Lahiri ayanamsa. "
            "<i>R</i> marks retrograde motion. House count is from the natal "
            "ascendant, whole-sign style.",
            styles["muted"],
        ),
        Spacer(1, 6),
        t,
    ]


def _karakas_block(karakas: dict, natal: Chart, styles: dict) -> list:
    rows = [["Role", "Planet", "Sign \u00b7 Degree", "House"]]
    for role, planet in karakas.items():
        p = natal.planets[planet]
        rows.append(
            [
                role,
                planet,
                f"{p.sign} {ve.degrees_to_dms(p.deg_in_sign)}",
                f"H{p.house}",
            ]
        )
    t = Table(rows, colWidths=[3.6 * cm, 2.4 * cm, 5.4 * cm, 1.6 * cm], repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GOLD),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.25, LINE),
            ]
        )
    )
    return [
        Paragraph("Jaimini Chara Karakas", styles["h1"]),
        Paragraph(
            "Each role is held by the planet at the highest degree among the "
            "seven core planets, descending. The Atmakaraka represents the "
            "soul's central agenda this lifetime.",
            styles["muted"],
        ),
        Spacer(1, 6),
        t,
    ]


def _dasha_section(natal: Chart, birth_jd: float, today_jd: float, styles: dict) -> list:
    moon_lon = natal.planets["Moon"].longitude
    dashas = ve.vimshottari_dasha(moon_lon, birth_jd)
    maha, antar, prat = ve.current_periods(dashas, today_jd)

    # Show the next ~50 years of mahadashas (truncate so we don't print 36)
    rows = [["Mahadasha", "From", "To", "Status"]]
    for lord, start, end in dashas:
        if end < today_jd - 365.25 * 5:
            continue  # skip very old chapters
        status = ""
        if start <= today_jd < end:
            pct = (today_jd - start) / (end - start) * 100
            status = f"active \u00b7 {pct:.0f}% in"
        elif end < today_jd:
            status = "past"
        else:
            status = "upcoming"
        rows.append([lord, ve.jd_to_date(start), ve.jd_to_date(end), status])
        if start > today_jd + 365.25 * 50:
            break

    t = Table(rows, colWidths=[3 * cm, 3.4 * cm, 3.4 * cm, 4.8 * cm], repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.25, LINE),
    ]
    # Highlight the active mahadasha row
    for i, row in enumerate(rows[1:], start=1):
        if "active" in row[3]:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), GOLD))
            style_cmds.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
            style_cmds.append(("FONT", (0, i), (-1, i), "Helvetica-Bold", 9))
    t.setStyle(TableStyle(style_cmds))

    out = [
        Paragraph("Vimshottari Dasha Timeline", styles["h1"]),
        Paragraph(
            "The 120-year planetary chapter cycle, anchored to the Moon's "
            "nakshatra at birth. The current chapter is highlighted.",
            styles["muted"],
        ),
        Spacer(1, 6),
        t,
    ]

    if maha:
        ml, ms, me = maha
        pct = (today_jd - ms) / (me - ms) * 100
        out += [
            Spacer(1, 10),
            Paragraph("Current Period", styles["h2"]),
            Paragraph(
                f"<b>Mahadasha:</b> {ml} \u00b7 {ve.jd_to_date(ms)} "
                f"\u2192 {ve.jd_to_date(me)} ({pct:.0f}% elapsed)",
                styles["body"],
            ),
        ]
        if antar:
            al, as_, ae = antar
            apct = (today_jd - as_) / (ae - as_) * 100
            out.append(
                Paragraph(
                    f"<b>Antardasha:</b> {al} \u00b7 {ve.jd_to_date(as_)} "
                    f"\u2192 {ve.jd_to_date(ae)} ({apct:.0f}% elapsed)",
                    styles["body"],
                )
            )
        if prat:
            pl, ps, pe = prat
            out.append(
                Paragraph(
                    f"<b>Pratyantar:</b> {pl} \u00b7 {ve.jd_to_date(ps)} "
                    f"\u2192 {ve.jd_to_date(pe)}",
                    styles["body"],
                )
            )
        out += [
            Spacer(1, 8),
            Paragraph(interp.MAHADASHA.get(ml, ""), styles["body"]),
        ]
    return out


def _panchanga_block(p: Panchanga, styles: dict) -> list:
    rows = [
        ["Vara (weekday)", p.vara],
        ["Tithi", f"{p.paksha} {p.tithi}"],
        ["Yoga", p.yoga],
        ["Karana", p.karana],
        ["Moon nakshatra", f"{p.moon_nakshatra} (pada {p.moon_pada})"],
        ["Sun-Moon distance", f"{p.sun_moon_diff:.2f}\u00b0"],
    ]
    t = Table(rows, colWidths=[4.2 * cm, 12 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                ("TEXTCOLOR", (0, 0), (0, -1), GOLD),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph("Panchanga at Birth", styles["h1"]),
        Paragraph(
            "The five-fold time signature: weekday, lunar day, yoga, karana, "
            "and the moon's nakshatra position at the moment of arrival.",
            styles["muted"],
        ),
        Spacer(1, 6),
        t,
    ]


def _blueprint_sections(natal: Chart, karakas: dict, styles: dict) -> list:
    out: list = [PageBreak(), Paragraph("Soul Blueprint", styles["title"])]
    out.append(
        HRFlowable(
            width="50%", thickness=0.4, color=GOLD, hAlign="CENTER", spaceBefore=2, spaceAfter=18
        )
    )

    # Ascendant
    out += [
        Paragraph("1. Core Identity (Ascendant)", styles["h1"]),
        Paragraph(
            f"<b>Rising:</b> {natal.ascendant_sign} \u00b7 "
            f"{ve.degrees_to_dms(natal.ascendant_deg)} \u00b7 "
            f"{natal.ascendant_nak} pada {natal.ascendant_pada}",
            styles["body"],
        ),
        Paragraph(interp.ASCENDANTS.get(natal.ascendant_sign, ""), styles["body"]),
    ]

    # Lagna lord
    lord = ve.LAGNA_LORDS[natal.ascendant_sign]
    lord_p = natal.planets[lord]
    out += [
        Paragraph("2. Lagna Lord", styles["h1"]),
        Paragraph(
            f"<b>{lord}</b> rules your ascendant. Its placement shows where "
            "your life energy is most concentrated.",
            styles["body"],
        ),
        Paragraph(
            f"It sits in <b>{lord_p.sign}</b> in the <b>{interp.ordinal(lord_p.house)} "
            f"house</b>, nakshatra <b>{lord_p.nakshatra} pada {lord_p.pada}</b>"
            f"{' (retrograde)' if lord_p.retrograde else ''}.",
            styles["body"],
        ),
        Paragraph(interp.planet_in_sign(lord, lord_p.sign), styles["body"]),
        Paragraph(
            f"Through the {interp.ordinal(lord_p.house)} house: "
            f"{interp.HOUSE_THEMES[lord_p.house]}",
            styles["body"],
        ),
    ]

    # Sun, Moon, then the rest
    section_idx = 3
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        p = natal.planets[planet]
        title = f"{section_idx}. {planet}"
        section_idx += 1
        retro = " (retrograde)" if p.retrograde else ""
        out += [
            Paragraph(title, styles["h1"]),
            Paragraph(
                f"<b>{p.sign}</b> \u00b7 {ve.degrees_to_dms(p.deg_in_sign)} "
                f"\u00b7 {p.nakshatra} pada {p.pada} \u00b7 "
                f"<b>{interp.ordinal(p.house)} house</b>{retro}",
                styles["body"],
            ),
            Paragraph(interp.planet_in_sign(planet, p.sign), styles["body"]),
            Paragraph(
                f"Through the {interp.ordinal(p.house)} house: {interp.HOUSE_THEMES[p.house]}",
                styles["body"],
            ),
        ]

    # Karaka highlight
    atma = karakas.get("Atmakaraka")
    dara = karakas.get("Darakaraka")
    if atma:
        ap = natal.planets[atma]
        out += [
            Paragraph(f"{section_idx}. Atmakaraka \u2014 the soul's signature", styles["h1"]),
            Paragraph(interp.KARAKA_BLURB["Atmakaraka"], styles["body"]),
            Paragraph(
                f"For you it is <b>{atma}</b> in <b>{ap.sign}</b>, "
                f"{interp.ordinal(ap.house)} house, "
                f"{ap.nakshatra} pada {ap.pada}. " + interp.planet_in_sign(atma, ap.sign),
                styles["body"],
            ),
        ]
        section_idx += 1
    if dara:
        dp = natal.planets[dara]
        out += [
            Paragraph(f"{section_idx}. Darakaraka \u2014 the partner the soul calls", styles["h1"]),
            Paragraph(interp.KARAKA_BLURB["Darakaraka"], styles["body"]),
            Paragraph(
                f"For you it is <b>{dara}</b> in <b>{dp.sign}</b>, "
                f"{interp.ordinal(dp.house)} house. " + interp.planet_in_sign(dara, dp.sign),
                styles["body"],
            ),
        ]

    return out


RED = colors.HexColor("#b91c1c")
GREEN = colors.HexColor("#15803d")


def _grid(extra: list | None = None) -> TableStyle:
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.25, LINE),
    ]
    return TableStyle(cmds + (extra or []))


def _yoga_section(natal: Chart, styles: dict) -> list:
    report = yg.detect_yogas(natal)
    out = [
        Paragraph("Yogas Formed", styles["h1"]),
        Paragraph(
            "Only combinations that this engine can prove from an explicit "
            "classical rule are listed, each with the text it comes from. If a "
            "yoga is absent, it did not form in this chart — the list is not "
            "abridged for length.",
            styles["muted"],
        ),
        Spacer(1, 6),
    ]
    if not report.formed:
        out.append(
            Paragraph(
                "<i>No yoga in the implemented rule set is formed in this chart.</i>",
                styles["body"],
            )
        )
        return out

    rows = [["Yoga", "How it forms here", "Source"]]
    for y in report.formed:
        label = y.name + (" [disputed]" if y.disputed else "")
        rows.append(
            [
                Paragraph(f"<b>{_esc(label)}</b>", styles["muted"]),
                Paragraph(_esc(y.detail) + _caveat(y.caveat), styles["muted"]),
                Paragraph(f"<i>{_esc(y.source)}</i>", styles["muted"]),
            ]
        )
    t = Table(rows, colWidths=[3.6 * cm, 8.4 * cm, 4.8 * cm], repeatRows=1)
    t.setStyle(_grid())
    out.append(t)
    return out


def _caveat(text: str | None) -> str:
    return f"<br/><i>{_esc(text)}</i>" if text else ""


def _strength_section(natal: Chart, styles: dict) -> list:
    strengths = sb.all_shadbala(natal)
    avr = av.compute_ashtakavarga(natal)

    rows = [["Planet", "Rupas", "Needs", "Band", "Sthana", "Dig", "Kala", "Cheshta", "Drik"]]
    for name, s in strengths.items():
        rows.append(
            [
                name,
                f"{s.total_rupas:.2f}",
                f"{s.required_rupas:.1f}",
                s.verdict,
                f"{s.sthana:.0f}",
                f"{s.dig:.0f}",
                f"{s.kala:.0f}",
                f"{s.cheshta:.0f}",
                f"{s.drik:.0f}",
            ]
        )
    t = Table(
        rows,
        colWidths=[2.4, 1.7, 1.5, 2.2, 1.9, 1.4, 1.4, 1.9, 1.5],
        repeatRows=1,
    )
    t._argW = [w * cm for w in t._argW]
    t.setStyle(_grid([("ALIGN", (1, 1), (-1, -1), "CENTER")]))

    sav = avr.sarva_by_house()
    sav_rows = [["House"] + [str(h) for h in range(1, 13)]]
    sav_rows.append(["Points"] + [str(sav[h]) for h in range(1, 13)])
    st = Table(sav_rows, colWidths=[1.9 * cm] + [1.21 * cm] * 12, repeatRows=1)
    st.setStyle(
        _grid(
            [
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 8),
            ]
        )
    )

    return [
        Paragraph("Strength", styles["h1"]),
        Paragraph(
            "Shadbala in rupas against the classical requirement for each graha. "
            "These totals omit varsha bala, masa bala and yuddha bala, which this "
            "engine does not compute, so they run slightly below a textbook figure "
            "and should be read as relative rather than absolute.",
            styles["muted"],
        ),
        Spacer(1, 6),
        t,
        Spacer(1, 10),
        Paragraph("Sarvashtakavarga by house", styles["h2"]),
        Paragraph(
            f"Out of 337 points across the chart. {av.SAV_RICH} or more is "
            f"classically strong, {av.SAV_POOR} or fewer thin.",
            styles["muted"],
        ),
        Spacer(1, 4),
        st,
    ]


def _evidence_section(natal: Chart, birth_jd: float, today_jd: float, styles: dict) -> list:
    report = ev.build_evidence(natal, birth_jd, today_jd)

    out = [
        PageBreak(),
        Paragraph("Evidence and What It Supports", styles["title"]),
        HRFlowable(
            width="50%", thickness=0.4, color=GOLD, hAlign="CENTER", spaceBefore=2, spaceAfter=14
        ),
        Paragraph(
            "Each area of life below was tested against nine kinds of chart "
            "factor. An area is reported only where at least two <i>different</i> "
            "kinds of factor agree; a kind that cancels itself out casts no vote. "
            "Areas that fail the test are listed as withheld rather than filled "
            "in with something plausible.",
            styles["body"],
        ),
        Spacer(1, 8),
    ]

    rows = [["H", "Area of life", "Reading", "Confidence", "Agreeing factors"]]
    style_extra = []
    for i, f in enumerate(report.findings, start=1):
        rows.append(
            [
                str(f.house),
                Paragraph(_esc(f.topic), styles["muted"]),
                Paragraph(_esc(f.verdict), styles["muted"]),
                f.confidence,
                Paragraph(_esc(", ".join(f.distinct_kinds)), styles["muted"]),
            ]
        )
        if f.verdict == "supported":
            style_extra.append(("TEXTCOLOR", (2, i), (2, i), GREEN))
        elif f.verdict == "under strain":
            style_extra.append(("TEXTCOLOR", (2, i), (2, i), RED))
    t = Table(rows, colWidths=[0.8 * cm, 4.0 * cm, 4.2 * cm, 2.6 * cm, 5.2 * cm], repeatRows=1)
    t.setStyle(_grid(style_extra))
    out.append(t)

    if report.withheld:
        out += [
            Spacer(1, 12),
            Paragraph("Withheld — not supportable from this chart", styles["h2"]),
            Paragraph(
                "These areas were tested and did not clear the threshold. That is "
                "a finding in itself, not an omission: any reading of them would "
                "be invention.",
                styles["muted"],
            ),
            Spacer(1, 4),
        ]
        wrows = [["H", "Area of life", "Why it is withheld"]]
        for w in report.withheld:
            wrows.append(
                [
                    str(w.house),
                    Paragraph(_esc(w.topic), styles["muted"]),
                    Paragraph(_esc(w.reason), styles["muted"]),
                ]
            )
        wt = Table(wrows, colWidths=[0.8 * cm, 4.0 * cm, 12.0 * cm], repeatRows=1)
        wt.setStyle(
            _grid(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), RED),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#fef2f2")],
                    ),
                ]
            )
        )
        out.append(wt)

    # The full ledger, so a practitioner can audit any single line.
    out += [
        PageBreak(),
        Paragraph("Evidence Ledger", styles["h1"]),
        Paragraph(
            "Every observation the engine made, with the arithmetic or placement "
            "behind it and the text it rests on. Findings above cite these ids.",
            styles["muted"],
        ),
        Spacer(1, 6),
    ]
    lrows = [["Id", "Kind", "Observation", "Basis and source"]]
    for e in report.ledger:
        mark = {1: "+", -1: "-", 0: "="}[e.polarity]
        # "[disputed]" rather than U+26A0: Helvetica has no warning sign,
        # so the marker that flagged contested material drew a black box --
        # exactly the material it is most important to label clearly.
        tag = f"{e.id} {mark}" + (" [disputed]" if e.disputed else "")
        lrows.append(
            [
                tag,
                Paragraph(_esc(e.kind.replace("_", " ")), styles["muted"]),
                Paragraph(_esc(e.statement), styles["muted"]),
                Paragraph(f"{_esc(e.basis)}<br/><i>{_esc(e.source)}</i>", styles["muted"]),
            ]
        )
    lt = Table(lrows, colWidths=[1.6 * cm, 2.4 * cm, 5.6 * cm, 7.2 * cm], repeatRows=1)
    lt.setStyle(_grid())
    out.append(lt)
    out.append(Spacer(1, 6))
    out.append(
        Paragraph(
            "A [disputed] tag marks material contested between authorities. It is "
            "shown for completeness and never counted toward the threshold.",
            styles["muted"],
        )
    )
    return out


def _activation_section(natal: Chart, birth_jd: float, today_jd: float, styles: dict) -> list:
    windows = tr.activation_windows(natal, birth_jd, today_jd, today_jd + 8 * 365.25)
    ss = tr.sade_sati(natal, today_jd)

    out = [
        PageBreak(),
        Paragraph("Timing: Where Dasha and Transit Converge", styles["h1"]),
        Paragraph(
            "A window opens where the running dasha lord is also being touched by "
            "a slow transit. Dates come from bisected ephemeris ingresses, not "
            "estimates. A window marks a live theme; it is not a prediction that "
            "a particular event will occur.",
            styles["muted"],
        ),
        Spacer(1, 8),
        Paragraph("Sade sati", styles["h2"]),
        Paragraph(
            _esc(f"{ss.phase} · {ss.window}" if ss.active and ss.window else ss.note),
            styles["body"],
        ),
        Spacer(1, 8),
    ]

    if not windows:
        out.append(Paragraph("<i>No convergence within the next eight years.</i>", styles["body"]))
        return out

    rows = [["From", "To", "Dasha", "Transit", "Why it converges"]]
    for w in windows[:24]:
        rows.append(
            [
                ve.jd_to_date(w.start_jd),
                ve.jd_to_date(w.end_jd),
                f"{w.mahadasha}/{w.antardasha}",
                f"{w.transiting} in {w.transit_sign}",
                Paragraph(_esc("; ".join(w.triggers)), styles["muted"]),
            ]
        )
    t = Table(rows, colWidths=[2.3 * cm, 2.3 * cm, 2.4 * cm, 3.0 * cm, 6.8 * cm], repeatRows=1)
    t.setStyle(_grid())
    out.append(t)
    return out


def _placements_section(natal: Chart, styles: dict) -> list:
    """What each graha is doing in the house it landed in.

    The report previously gave positions and gave results, with nothing in
    between: a reader could see "Saturn 27°36' Capricorn, house 10" and could
    see a verdict, but nothing said what Saturn in the tenth house *means*.
    """
    dig = natal.dignities if hasattr(natal, "dignities") else None
    out: list = [
        PageBreak(),
        Paragraph("Each Planet, and What It Is Doing", styles["title"]),
        Paragraph(
            "What the classical texts hold each graha to signify in the bhava "
            "it occupies in this chart, the strengths it offers and the "
            "weaknesses it carries there, how it colours temperament, and the "
            "classical upaya for that graha. Strengths and weaknesses are "
            "weighted by the dignity the planet actually holds here, so the "
            "same placement does not read identically in every chart.",
            styles["muted"],
        ),
        Spacer(1, 10),
    ]

    from .dignity import all_dignities

    dig = all_dignities(natal)

    for name in ve.VEDIC_PLANETS:
        p = natal.planets[name]
        d = dig[name]
        r = plc.placement_reading(
            name,
            p.house,
            p.sign,
            d.state,
            retrograde=p.retrograde,
            combust=d.combust,
        )
        out.append(
            Paragraph(
                f"{_sigil(name)} &nbsp;<b>{_esc(name)}</b> in house {p.house} "
                f"&mdash; {_esc(p.sign)}, {_esc(d.state)}"
                + (" (retrograde)" if p.retrograde else ""),
                styles["h2"],
            )
        )
        out.append(Paragraph(_esc(r.signifies), styles["body"]))
        out.append(Paragraph(f"<b>Strengths.</b> {_esc(r.strengths)}", styles["body"]))
        out.append(Paragraph(f"<b>Weaknesses.</b> {_esc(r.weaknesses)}", styles["body"]))
        out.append(Paragraph(f"<b>Temperament.</b> {_esc(r.nature)}", styles["body"]))
        if r.notable:
            out.append(Paragraph(_esc(r.notable), styles["muted"]))
        out.append(Paragraph(f"<i>{_esc(r.condition)}</i>", styles["body"]))
        out.append(
            Paragraph(
                f"<b>Upaya ({_esc(r.remedy['graha'])}).</b> "
                f"{_esc(r.remedy['transliteration'])} &middot; "
                f"{_esc(r.remedy['vara'])} &middot; daana: "
                f"{_esc(r.remedy['daana'])} &middot; ratna: "
                f"{_esc(r.remedy['gem'])}. {_esc(r.remedy['practical'])}",
                styles["body"],
            )
        )
        out.append(Spacer(1, 8))

    out.append(Paragraph(_esc(plc.REMEDY_CAVEAT) + " " + _esc(plc.RATNA_CAVEAT), styles["muted"]))
    return out


def _all_houses_section(natal: Chart, styles: dict) -> list:
    """Every bhava's significance, including the ones the gate withheld.

    Describing what a house governs is structure, not prediction, so it needs
    no corroboration -- which is why it can be given for all twelve while the
    findings remain gated.
    """
    from .aspects import house_lord, house_sign
    from .dignity import all_dignities

    dig = all_dignities(natal)
    avr = av.compute_ashtakavarga(natal)

    rows = [["House", "Governs", "Sign", "Lord · where it went", "SAV"]]
    for h in range(1, 13):
        lord = house_lord(natal, h)
        lp = natal.planets[lord]
        occupants = [n for n in ve.VEDIC_PLANETS if natal.planets[n].house == h]
        occ = ", ".join(ABBREV[n] for n in occupants) or "—"
        rows.append(
            [
                f"{h}\n{occ}",
                ev.HOUSE_TOPICS[h],
                house_sign(natal, h),
                f"{lord} → h{lp.house} ({dig[lord].state})",
                str(avr.sarva_in_house(h)),
            ]
        )

    t = Table(
        rows,
        colWidths=[1.7 * cm, 5.6 * cm, 2.3 * cm, 5.2 * cm, 1.2 * cm],
        repeatRows=1,
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
                ("ALIGN", (4, 0), (4, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.25, LINE),
            ]
        )
    )

    out: list = [
        PageBreak(),
        Paragraph("All Twelve Houses", styles["title"]),
        Paragraph(
            "The structure of the whole chart, including the houses no reading "
            "was given for. What a bhava governs and who rules it is not a "
            "claim about a life, so it needs no corroboration.",
            styles["muted"],
        ),
        Spacer(1, 8),
        t,
        Spacer(1, 12),
    ]
    for h in range(1, 13):
        out.append(
            Paragraph(
                f"<b>House {h} &mdash; {_esc(ev.HOUSE_TOPICS[h])}.</b> "
                f"{_esc(interp.HOUSE_GOVERNS[h])}",
                styles["body"],
            )
        )
    return out


def _numerology_section(name: str, year: int, month: int, day: int, styles: dict) -> list:
    """Beside the chart, and outside the gate. See kosma.numerology."""
    from datetime import date as _date

    n = numero.compute(name or "", _date(year, month, day))
    out: list = [
        PageBreak(),
        Paragraph("Numerology", styles["title"]),
        Paragraph(_esc(n["note"]), styles["muted"]),
        Spacer(1, 8),
    ]
    entries = [
        ("Mulank (root number)", n["mulank"]),
        ("Bhagyank (destiny number)", n["bhagyank"]),
        ("Name — Chaldean", n["name_chaldean"]),
        ("Name — Pythagorean", n["name_pythagorean"]),
    ]
    rows = [["", "No.", "Graha", "Meaning"]]
    for label, entry in entries:
        if not entry:
            continue
        rows.append([label, str(entry["number"]), entry["graha"], entry["meaning"]])
    t = Table(rows, colWidths=[4.4 * cm, 1.2 * cm, 2.0 * cm, 8.4 * cm], repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.25, LINE),
            ]
        )
    )
    out.append(t)
    if n.get("disagreement"):
        out += [Spacer(1, 8), Paragraph(_esc(n["disagreement"]), styles["body"])]
    if n["name_chaldean"] or n["name_pythagorean"]:
        out += [Spacer(1, 6), Paragraph(_esc(n["name_note"]), styles["muted"])]
    return out


def _disclaimer(styles: dict) -> list:
    return [
        Spacer(1, 14),
        HRFlowable(width="100%", thickness=0.3, color=LINE, spaceBefore=6, spaceAfter=10),
        Paragraph("Notes & Privacy", styles["h2"]),
        Paragraph(
            "This report is generated entirely in memory at the moment of your "
            "request and is not stored on the server, in logs, or in any "
            "database. The PDF you receive is the only artefact created from "
            "your birth data.",
            styles["body"],
        ),
        Paragraph(
            "Calculations use the Swiss Ephemeris with Lahiri (Chitrapaksha) "
            "ayanamsa, the standard for Vedic astrology. Birth-time accuracy "
            "matters: the ascendant changes sign roughly every two hours, and "
            "a ten-minute error can shift the nakshatra pada.",
            styles["body"],
        ),
        Paragraph(
            "This document is for self-reflection. It is not a substitute for "
            "medical, legal, financial, or psychological advice.",
            styles["body"],
        ),
    ]


# ── Footer ────────────────────────────────────────────────────────────


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(
        A4[0] / 2,
        1.2 * cm,
        f"KOSMA  \u00b7  page {doc.page}  \u00b7  generated "
        f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%MZ')} UTC",
    )
    canvas.restoreState()


# ── Public API ────────────────────────────────────────────────────────


def _esc(s: str) -> str:
    """Minimal escaping for ReportLab paragraph XML."""
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_pdf(
    *,
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    place: str,
    today: datetime | None = None,
) -> bytes:
    """Render the full Soul Blueprint to a PDF byte string."""
    today = today or datetime.now(UTC)

    natal = ve.build_chart(
        label=name or "Anonymous",
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=lat,
        lon_geo=lon,
        tz=tz,
    )
    karakas = ve.jaimini_karakas(natal)
    panchanga = ve.panchanga_for(natal)

    birth_jd = ve.local_to_ut(year, month, day, hour, minute, tz)
    today_jd = ve.local_to_ut(
        today.year,
        today.month,
        today.day,
        today.hour,
        today.minute,
        0.0,  # today computed in UTC
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="KOSMA Soul Blueprint",
        author="KOSMA",
        subject="Vedic chart, computed in memory and not retained",
        creator="KOSMA",
        # `invariant` zeroes the embedded /CreationDate and /ModDate. Those
        # timestamps record to the second when a person generated a reading,
        # which is metadata about them that survives in the file they keep and
        # in anything they forward it to. The visible footer already carries a
        # date for the reader; the file does not also need a hidden one.
        invariant=True,
    )
    styles = _styles()

    story: list = []
    story += _cover(name, (year, month, day), (hour, minute), place, styles)
    story += _birth_summary(natal, place, styles)
    story += [Spacer(1, 6)]
    story += _wheel_section(natal, styles)
    story += [PageBreak()]
    story += _planet_table(natal, styles)
    story += [Spacer(1, 12)]
    story += _karakas_block(karakas, natal, styles)
    story += [Spacer(1, 12)]
    story += _navamsa_table(natal, styles)
    story += [Spacer(1, 12)]
    story += _panchanga_block(panchanga, styles)
    story += [Spacer(1, 12)]
    story += _dasha_section(natal, birth_jd, today_jd, styles)
    story += [PageBreak()]
    story += _yoga_section(natal, styles)
    story += [Spacer(1, 12)]
    story += _strength_section(natal, styles)
    story += _evidence_section(natal, birth_jd, today_jd, styles)
    story += _activation_section(natal, birth_jd, today_jd, styles)
    story += _placements_section(natal, styles)
    story += _all_houses_section(natal, styles)
    story += _blueprint_sections(natal, karakas, styles)
    story += _numerology_section(name, year, month, day, styles)
    story += _disclaimer(styles)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
