"""The grounding pack, the prompt, the CLI, memory, and the API route."""

from __future__ import annotations

import json
from itertools import pairwise

import pytest

from kosma import grounding, memory
from kosma import transits as tr
from kosma import vedic_engine as ve

# ── pack shape ────────────────────────────────────────────────────────


def test_pack_is_json_serialisable(reference_pack: dict) -> None:
    text = grounding.to_json(reference_pack)
    assert json.loads(text) is not None


def test_pack_has_every_top_level_section(reference_pack: dict) -> None:
    expected = {
        "meta",
        "birth",
        "ascendant",
        "houses",
        "planets",
        "conjunctions",
        "mutual_aspects",
        "chains",
        "panchanga",
        "jaimini_karakas",
        "vargas",
        "ashtakavarga",
        "kp",
        "yogas",
        "dasha",
        "transits",
        "activation_windows",
        "evidence",
        "constraints",
    }
    assert expected <= set(reference_pack)


def test_pack_declares_its_calculation_basis(reference_pack: dict) -> None:
    meta = reference_pack["meta"]
    assert meta["zodiac"] == "sidereal"
    assert "Lahiri" in meta["ayanamsa"]
    assert "Swiss Ephemeris" in meta["ephemeris"]
    assert "No Western/tropical" in meta["tradition"]


def test_pack_matches_the_pinned_reference_chart(reference_pack: dict) -> None:
    asc = reference_pack["ascendant"]
    assert asc["sign"] == "Aries"
    assert asc["nakshatra"]["name"] == "Ashwini"
    assert asc["nakshatra"]["pada"] == 1
    assert asc["kp_chain"] == {
        "star_lord": "Ketu",
        "sub_lord": "Ketu",
        "sub_sub_lord": "Venus",
    }
    assert reference_pack["jaimini_karakas"]["Atmakaraka"] == "Moon"


def test_every_planet_block_is_complete(reference_pack: dict) -> None:
    assert len(reference_pack["planets"]) == len(ve.VEDIC_PLANETS)
    for p in reference_pack["planets"]:
        assert p["nakshatra"]["name"]
        assert p["nakshatra"]["deity"], "nakshatra must carry its deity, not just a name"
        assert p["nakshatra"]["pada_lord"]
        assert p["dignity"]["why"], "dignity must explain itself"
        assert p["kp_chain"]["sub_lord"]
        if p["name"] not in ("Rahu", "Ketu"):
            assert "shadbala" in p
            assert p["shadbala"]["omitted_components"], "omissions must be declared"
            assert p["shadbala"]["complete"] is False


def test_constraints_forbid_recalculation_and_invention(reference_pack: dict) -> None:
    joined = " ".join(reference_pack["constraints"]).lower()
    assert "do not calculate" in joined
    assert "yoga" in joined
    assert "withheld" in joined


def test_withheld_topics_are_named_in_the_pack(reference_pack: dict) -> None:
    ev = reference_pack["evidence"]
    assert "gate" in ev and str(ev["minimum_agreeing_kinds"]) in ev["gate"]
    for w in ev["withheld"]:
        assert w["reason"]
        assert 1 <= w["house"] <= 12


def test_activation_windows_are_ordered_and_bounded(reference_pack: dict) -> None:
    windows = reference_pack["activation_windows"]["windows"]
    for w in windows:
        assert w["days"] > 0
        assert w["triggers"]
        assert w["converging_factors"] >= 2
    assert "not events" in reference_pack["activation_windows"]["caveat"]


def test_pack_states_the_no_storage_posture(reference_pack: dict) -> None:
    assert "not written to disk" in reference_pack["birth"]["storage_note"].lower()
    assert "ascendant moves" in reference_pack["birth"]["accuracy_note"]


# ── prompt ────────────────────────────────────────────────────────────


def test_system_prompt_binds_the_model_to_the_pack() -> None:
    prompt = grounding.system_prompt()
    lowered = prompt.lower()
    assert "you do not calculate" in lowered
    assert "withheld" in lowered
    assert "cite" in lowered
    # The persona must not be allowed to override the honesty requirement.
    assert "does not clearly show" in lowered or "chart is silent" in lowered


def test_bundle_contains_both_halves(reference_pack: dict) -> None:
    text = grounding.bundle(reference_pack)
    assert "GROUNDING PACK" in text
    assert "Jyotish Acharya" in text
    assert '"ascendant"' in text


# ── transits ──────────────────────────────────────────────────────────


def test_sign_spans_tile_the_window_without_gaps(reference_chart: ve.Chart) -> None:
    start = reference_chart.jd
    end = start + 365.25 * 6
    spans = tr.sign_spans("Jupiter", start, end)
    assert spans[0].start_jd == pytest.approx(start)
    assert spans[-1].end_jd == pytest.approx(end)
    for a, b in pairwise(spans):
        assert a.end_jd == pytest.approx(b.start_jd)


def test_ingress_dates_land_on_a_sign_boundary(reference_chart: ve.Chart) -> None:
    start = reference_chart.jd
    ingresses = tr.sign_ingresses("Saturn", start, start + 365.25 * 12)
    assert ingresses, "Saturn changes sign several times in twelve years"
    for ing in ingresses:
        before = tr._lon_at(ing.jd - 0.01, "Saturn") % 30
        after = tr._lon_at(ing.jd + 0.01, "Saturn") % 30
        # One side is just below 30 degrees and the other just above 0.
        assert min(before, 30 - before, after, 30 - after) < 0.05


def test_sade_sati_reports_a_phase_only_when_active(
    reference_chart: ve.Chart, pinned_now_jd: float
) -> None:
    ss = tr.sade_sati(reference_chart, pinned_now_jd)
    if ss.active:
        assert ss.phase and ss.window
    else:
        assert ss.phase is None


# ── memory ────────────────────────────────────────────────────────────


def test_memory_roundtrip(tmp_path, reference_pack: dict) -> None:
    record = memory.new_record(reference_pack, label="Reference")
    record.add_note("career", "Started a new role.")
    path = memory.save(tmp_path / "m.kosma", record, "correct horse battery")

    loaded = memory.load(path, "correct horse battery")
    assert loaded.chart_fingerprint == record.chart_fingerprint
    assert loaded.notes[0]["topic"] == "career"
    assert memory.verify(loaded, reference_pack)


def test_memory_file_is_not_readable_without_the_passphrase(tmp_path, reference_pack: dict) -> None:
    record = memory.new_record(reference_pack)
    record.add_note("marriage", "a private note that must not leak")
    path = memory.save(tmp_path / "m.kosma", record, "passphrase one")

    raw = path.read_text(encoding="utf-8")
    assert "private note" not in raw
    assert "London" not in raw

    with pytest.raises(ValueError):
        memory.load(path, "the wrong passphrase")


def test_fingerprint_identifies_the_chart_without_the_birth_data(
    reference_pack: dict,
) -> None:
    fp = memory.fingerprint(reference_pack)
    assert len(fp) == 32
    assert reference_pack["birth"]["place"] not in fp
    assert reference_pack["birth"]["local_datetime"] not in fp


def test_mismatched_memory_is_flagged_not_silently_trusted(
    reference_pack: dict, second_chart: ve.Chart, pinned_now
) -> None:
    other = grounding.build_pack(
        grounding.BirthInput(
            name="Epoch B",
            year=2010,
            month=6,
            day=21,
            hour=6,
            minute=0,
            lat=22.7196,
            lon=75.8577,
            tz=5.5,
            place="Indore, India",
        ),
        now=pinned_now,
    )
    record = memory.new_record(other)
    merged = memory.merge_into_pack(dict(reference_pack), record)
    assert merged["memory"]["matches_this_chart"] is False
    assert merged["memory"]["warning"]


def test_memory_is_marked_as_context_not_instruction(reference_pack: dict) -> None:
    record = memory.new_record(reference_pack)
    merged = memory.merge_into_pack(dict(reference_pack), record)
    assert "not instruction" in merged["memory"]["handling"]


# ── CLI ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("fmt", ["json", "report", "bundle", "prompt"])
def test_cli_formats_run(tmp_path, fmt: str) -> None:
    from kosma.cli import main

    out = tmp_path / f"out.{fmt}"
    code = main(
        [
            "--date",
            "2000-01-01",
            "--time",
            "12:00",
            "--city",
            "London, UK",
            "--as-of",
            "2026-08-08",
            "--format",
            fmt,
            "--out",
            str(out),
        ]
    )
    assert code == 0
    assert out.read_text(encoding="utf-8").strip()


def test_cli_rejects_an_unknown_city() -> None:
    from kosma.cli import main

    with pytest.raises(SystemExit):
        main(["--date", "2000-01-01", "--time", "12:00", "--city", "Atlantis"])


def test_cli_requires_a_date() -> None:
    from kosma.cli import main

    with pytest.raises(SystemExit):
        main(["--time", "12:00", "--city", "London, UK"])


def test_cli_lists_cities_without_a_birth_date(capsys) -> None:
    from kosma.cli import main

    assert main(["--list-cities"]) == 0
    assert "London, UK" in capsys.readouterr().out
