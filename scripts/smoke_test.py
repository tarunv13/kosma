"""
Smoke test for the engine and PDF generator.

Reference chart — the J2000.0 epoch, not a person:
    DOB:  1 Jan 2000
    TOB:  12:00 UT
    POB:  London (51.5074 N, 0.1278 W, +0:00)

Expected ascendant: Aries ~0 09' (Ashwini pada 1,
                                  KP Ketu / Ketu / Venus)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kosma import pdf_generator
from kosma import vedic_engine as ve


def main() -> int:
    chart = ve.build_chart(
        label="Test Subject",
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=51.5074,
        lon_geo=-0.1278,
        tz=0.0,
    )
    print(f"Ascendant      : {chart.ascendant_sign} {ve.degrees_to_dms(chart.ascendant_deg)}")
    print(f"Asc nakshatra  : {chart.ascendant_nak} pada {chart.ascendant_pada}")
    print(f"Asc KP chain   : {'/'.join(chart.ascendant_kp)}")
    print(f"Ayanamsa       : {chart.ayanamsa:.4f} deg")
    print()
    print(f"{'Planet':<10} {'Sign':<13} {'Deg':<14} {'Nakshatra':<22} P  H")
    print("-" * 72)
    for name in ve.VEDIC_PLANETS:
        p = chart.planets[name]
        retro = " R" if p.retrograde else "  "
        print(
            f"{name + retro:<10} {p.sign:<13} {ve.degrees_to_dms(p.deg_in_sign):<14} "
            f"{p.nakshatra:<22} {p.pada}  {p.house}"
        )

    karakas = ve.jaimini_karakas(chart)
    print()
    print("Jaimini karakas:")
    for role, planet in karakas.items():
        p = chart.planets[planet]
        print(f"  {role:<14}: {planet} ({p.sign} {ve.degrees_to_dms(p.deg_in_sign)}, H{p.house})")

    # Spec assertions (loose: within 0.1 deg of expected)
    assert chart.ascendant_sign == "Aries", chart.ascendant_sign
    assert chart.ascendant_nak == "Ashwini", chart.ascendant_nak
    assert 0.0 < chart.ascendant_deg < 1.0, chart.ascendant_deg
    print("\nAscendant assertion passed.")

    # PDF generation
    pdf = pdf_generator.generate_pdf(
        name="Epoch J2000",
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=51.5074,
        lon=-0.1278,
        tz=0.0,
        place="London, UK",
    )
    out = Path(__file__).parent / "out_test.pdf"
    out.write_bytes(pdf)
    print(f"\nPDF generated: {out} ({len(pdf):,} bytes)")
    assert pdf.startswith(b"%PDF-"), "Not a valid PDF"
    print("PDF magic bytes ok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
