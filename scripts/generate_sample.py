"""
Regenerate ``docs/sample-blueprint.pdf`` for the v1.0 reference chart.

Used by `make sample` and committed so the repo always carries a current
example PDF that matches the engine's output. Anyone landing on the README
can see exactly what the report looks like without running the app.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kosma import pdf_generator


def main() -> int:
    out = Path(__file__).resolve().parent.parent / "docs" / "sample-blueprint.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Pin the "today" date so the dasha tables and "X% elapsed" numbers stay
    # deterministic across regenerations. This keeps the file stable in git
    # diffs and makes the README sample link reliable.
    today = datetime(2026, 5, 25, tzinfo=UTC)

    pdf = pdf_generator.generate_pdf(
        # The J2000.0 epoch at the prime meridian. Synthetic on purpose: a
        # sample report committed to a public repository must not carry a
        # real person's birth data.
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
        today=today,
    )
    out.write_bytes(pdf)
    print(f"wrote {out} ({len(pdf):,} bytes) for today={today:%Y-%m-%d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
