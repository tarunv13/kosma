"""
Command-line entry point.

Produces the grounding pack, the prompt-plus-pack bundle, a readable text
report, or the PDF — all locally, with nothing leaving the machine.

    python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK"
    python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK" --format bundle
    python -m kosma --date 2000-01-01 --time 12:00 --lat 51.5074 --lon -0.1278 --tz 0
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from . import __version__, cities, grounding
from .grounding import BirthInput

FORMATS = ("json", "prompt", "bundle", "report", "pdf")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="kosma",
        description=(
            "Compute a Vedic chart and emit a grounding pack that an AI can "
            "interpret without calculating anything itself."
        ),
        epilog=(
            "Birth data is used in memory and discarded. Nothing is uploaded, "
            "logged, or written to disk unless you pass --out."
        ),
    )
    p.add_argument("--version", action="version", version=f"KOSMA {__version__}")
    p.add_argument("--name", default="", help="name for the report header")
    # Not marked required, so that --list-cities works on its own; the check
    # happens in main() once that flag has been handled.
    p.add_argument("--date", metavar="YYYY-MM-DD", help="birth date (required)")
    p.add_argument("--time", metavar="HH:MM", help="birth time, 24-hour local (required)")

    place = p.add_argument_group("place (give --city, or all of --lat/--lon/--tz)")
    place.add_argument("--city", default="", help="city from the built-in table")
    place.add_argument("--lat", type=float, help="latitude, -90 to 90")
    place.add_argument("--lon", type=float, help="longitude, -180 to 180")
    place.add_argument("--tz", type=float, help="UTC offset in hours at birth, e.g. 5.5")
    place.add_argument("--place", default="", help="label for manual coordinates")
    place.add_argument("--list-cities", action="store_true", help="print the city table and exit")

    out = p.add_argument_group("output")
    out.add_argument("--format", choices=FORMATS, default="json", help="what to emit")
    out.add_argument("--out", metavar="FILE", help="write to a file instead of stdout")
    out.add_argument(
        "--as-of",
        metavar="YYYY-MM-DD",
        help="compute transits and dashas as of this date instead of today",
    )
    out.add_argument(
        "--horizon",
        type=float,
        default=8.0,
        metavar="YEARS",
        help="how far ahead to scan for activation windows (default 8)",
    )
    out.add_argument("--compact", action="store_true", help="minified JSON")

    mem = p.add_argument_group("memory (optional, held by you and never uploaded)")
    mem.add_argument("--memory", metavar="FILE", help="attach or create an encrypted memory file")
    mem.add_argument(
        "--passphrase",
        metavar="TEXT",
        help="passphrase for the memory file; prompted for if omitted",
    )
    return p


def _resolve_place(args: argparse.Namespace) -> tuple[float, float, float, str]:
    if args.city:
        coords = cities.lookup(args.city)
        if coords is None:
            raise SystemExit(
                f"Unknown city {args.city!r}. Run --list-cities, or give --lat/--lon/--tz instead."
            )
        lat, lon, tz = coords
        return lat, lon, tz, args.city
    if args.lat is None or args.lon is None or args.tz is None:
        raise SystemExit("Give --city, or all three of --lat, --lon and --tz.")
    if not -90.0 <= args.lat <= 90.0:
        raise SystemExit("--lat must be between -90 and 90.")
    if not -180.0 <= args.lon <= 180.0:
        raise SystemExit("--lon must be between -180 and 180.")
    if not -14.0 <= args.tz <= 14.0:
        raise SystemExit("--tz must be between -14 and 14.")
    return args.lat, args.lon, args.tz, (args.place or "Custom location")


def _parse_when(args: argparse.Namespace) -> tuple[int, int, int, int, int]:
    try:
        d = date.fromisoformat(args.date)
    except ValueError:
        raise SystemExit(f"Bad --date {args.date!r}; expected YYYY-MM-DD.") from None
    try:
        hh, mm = args.time.split(":")
        hour, minute = int(hh), int(mm)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        raise SystemExit(f"Bad --time {args.time!r}; expected HH:MM in 24-hour form.") from None
    return d.year, d.month, d.day, hour, minute


def _text_report(pack: dict) -> str:
    """A readable summary. Deliberately structural — it does not interpret."""
    lines: list[str] = []
    add = lines.append

    asc = pack["ascendant"]
    add("=" * 72)
    add(f"KOSMA grounding report  |  {pack['meta']['generator']}")
    add("=" * 72)
    add(
        f"Born      {pack['birth']['local_datetime']}  UTC{pack['birth']['timezone_offset_hours']:+g}"
    )
    add(f"Place     {pack['birth']['place']}")
    add(f"Ayanamsa  {pack['meta']['ayanamsa']} ({pack['meta']['ayanamsa_value_deg']:.4f} deg)")
    add(
        f"Lagna     {asc['sign']} {asc['degree_dms']}  |  {asc['nakshatra']['name']} "
        f"pada {asc['nakshatra']['pada']}  |  KP {asc['kp_chain']['star_lord']}/"
        f"{asc['kp_chain']['sub_lord']}/{asc['kp_chain']['sub_sub_lord']}"
    )
    add("")

    add("-- Planets " + "-" * 61)
    add(
        f"{'Body':9s} {'Sign':12s} {'Degree':12s} {'H':>2s}  {'Nakshatra':20s} {'Dignity':22s} Bala"
    )
    for p in pack["planets"]:
        bala = p.get("shadbala")
        # Shadbala is defined for the seven grahas only, so the nodes get a
        # dash rather than a misleading zero.
        bala_cell = f"{bala['total_rupas']:.2f}" if bala else "  -"
        add(
            f"{p['name']:9s} {p['sign']:12s} {p['degree_dms']:12s} "
            f"{p['house_whole_sign']:2d}  "
            f"{p['nakshatra']['name'][:18]:20s} "
            f"{p['dignity']['state'][:20]:22s} "
            f"{bala_cell}"
        )
    add("")

    add("-- Yogas formed " + "-" * 56)
    if not pack["yogas"]["formed"]:
        add("  none formed under the implemented rule set")
    for y in pack["yogas"]["formed"]:
        flag = "  [disputed]" if y["disputed"] else ""
        add(f"  {y['name']}{flag}")
        add(f"      {y['detail']}")
        add(f"      source: {y['source']}")
    add("")

    cur = pack["dasha"]["current"]
    add("-- Dasha " + "-" * 63)
    for level in ("mahadasha", "antardasha", "pratyantardasha"):
        v = cur.get(level)
        if v:
            add(f"  {level:16s} {v['lord']:9s} {v['from']} -> {v['to']}")
    add("")

    add("-- Transits " + "-" * 60)
    for name, t in pack["transits"]["positions"].items():
        cond = f"  <- {t['classical_condition']}" if t["classical_condition"] else ""
        add(
            f"  {name:9s} {t['sign']:12s} H{t['house_from_lagna']:<2d} from lagna, "
            f"H{t['house_from_moon']:<2d} from Moon{cond}"
        )
    ss = pack["transits"]["sade_sati"]
    add(f"  Sade sati: {'running - ' + str(ss['phase']) if ss['active'] else 'not running'}")
    if ss["window"]:
        add(f"             {ss['window']}")
    add("")

    add("-- Evidence gate " + "-" * 55)
    add(f"  {pack['evidence']['gate']}")
    add("")
    for f in pack["evidence"]["findings"]:
        add(f"  H{f['house']:<2d} {f['topic']}")
        add(
            f"       {f['verdict']}  ({f['confidence']}; {len(f['agreeing_kinds'])} agreeing kinds)"
        )
        add(f"       citations: {', '.join(f['citations'][:8])}")
    if pack["evidence"]["withheld"]:
        add("")
        add("  WITHHELD - not supportable from this chart, do not interpret:")
        for w in pack["evidence"]["withheld"]:
            add(f"    H{w['house']:<2d} {w['topic']}")
            add(f"         {w['reason']}")
    add("")

    wins = pack["activation_windows"]["windows"]
    add("-- Activation windows " + "-" * 50)
    if not wins:
        add("  none within the horizon")
    for w in wins[:12]:
        add(
            f"  {w['from']:>12s} -> {w['to']:<12s} {w['mahadasha']}/{w['antardasha']:<9s} "
            f"{w['transiting']} in {w['transit_sign']}"
        )
    add(f"  {pack['activation_windows']['caveat']}")
    add("")
    add("=" * 72)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.list_cities:
        for name in cities.city_names():
            print(name)
        return 0

    missing = [flag for flag, value in (("--date", args.date), ("--time", args.time)) if not value]
    if missing:
        raise SystemExit(f"Missing required argument(s): {', '.join(missing)}")

    year, month, day, hour, minute = _parse_when(args)
    lat, lon, tz, place = _resolve_place(args)

    now = datetime.now(UTC)
    if args.as_of:
        try:
            d = date.fromisoformat(args.as_of)
        except ValueError:
            raise SystemExit(f"Bad --as-of {args.as_of!r}; expected YYYY-MM-DD.") from None
        now = datetime(d.year, d.month, d.day, 12, 0, tzinfo=UTC)

    birth = BirthInput(
        name=args.name.strip()[:80],
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=lat,
        lon=lon,
        tz=tz,
        place=place,
    )

    if args.format == "pdf":
        from . import pdf_generator

        payload: str | bytes = pdf_generator.generate_pdf(
            name=birth.name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            lat=lat,
            lon=lon,
            tz=tz,
            place=place,
            today=now,
        )
        if not args.out:
            raise SystemExit("--format pdf needs --out FILE.")
        Path(args.out).write_bytes(payload)  # type: ignore[arg-type]
        print(f"Wrote {args.out}", file=sys.stderr)
        return 0

    pack = grounding.build_pack(birth, now=now, activation_years=args.horizon)

    if args.memory:
        payload_mem = _handle_memory(args, pack)
        if payload_mem is not None:
            pack = payload_mem

    if args.format == "json":
        text = grounding.to_json(pack, indent=None if args.compact else 2)
    elif args.format == "prompt":
        text = grounding.system_prompt()
    elif args.format == "bundle":
        text = grounding.bundle(pack)
    else:
        text = _text_report(pack)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        print(text)
    return 0


def _handle_memory(args: argparse.Namespace, pack: dict) -> dict | None:
    """Create or attach an encrypted memory file, then merge it into the pack."""
    from getpass import getpass

    from . import memory

    passphrase = args.passphrase or getpass("Memory passphrase: ")
    if not passphrase:
        print("No passphrase given; skipping memory.", file=sys.stderr)
        return None

    path = Path(args.memory)
    try:
        if path.exists():
            record = memory.load(path, passphrase)
            if not memory.verify(record, pack):
                print(
                    "Warning: this memory file was written for a different chart.",
                    file=sys.stderr,
                )
        else:
            record = memory.new_record(pack, label=args.name)
            memory.save(path, record, passphrase)
            print(f"Created encrypted memory at {path}", file=sys.stderr)
    except (RuntimeError, ValueError) as exc:
        print(f"Memory unavailable: {exc}", file=sys.stderr)
        return None

    record.last_dasha_seen = pack["dasha"]["current"]
    record.updated_at = pack["meta"]["computed_at_utc"]
    memory.save(path, record, passphrase)
    return memory.merge_into_pack(pack, record)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
