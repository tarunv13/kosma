"""The wire contract between the engine and any frontend.

These tests exist because the TypeScript interfaces in `web/src/types/chart.ts`
are the same contract written twice. If a field is renamed here and not there,
the client renders undefined; these assertions make that a red build instead.
"""

from __future__ import annotations

import json
from itertools import pairwise

import pytest

from kosma import api_contract as ac
from kosma import vedic_engine as ve

REFERENCE = {
    "name": "Epoch J2000",
    "year": 2000,
    "month": 1,
    "day": 1,
    "hour": 12,
    "minute": 0,
    "lat": 51.5074,
    "lon": -0.1278,
    "tz": 0.0,
    "place": "London, UK",
}


@pytest.fixture(scope="module")
def payload(pinned_now):
    return ac.build_chart_payload(**REFERENCE, now=pinned_now)


def test_payload_is_json_serialisable(payload: dict) -> None:
    assert json.loads(json.dumps(payload)) is not None


def test_declares_its_contract_version(payload: dict) -> None:
    assert payload["contract_version"] == ac.CONTRACT_VERSION
    major = payload["contract_version"].split(".")[0]
    assert major.isdigit(), "the client compares major versions, so it must parse"


def test_top_level_shape(payload: dict) -> None:
    expected = {
        "contract_version",
        "chart_meta",
        "ascendant",
        "planets",
        "houses",
        "vargas",
        "panchanga",
        "yogas",
        "dashas",
        "findings",
        "withheld",
        "evidence",
        "gate",
        "disclaimer",
    }
    assert set(payload) == expected


def test_planet_fields_match_the_typescript_interface(payload: dict) -> None:
    required = {
        "id",
        "name",
        "glyph",
        "long",
        "speed",
        "degree",
        "degree_dms",
        "sign",
        "sign_index",
        "house_index",
        "nakshatra",
        "pada",
        "nakshatra_lord",
        "nakshatra_deity",
        "retrograde",
        "combust",
        "sandhi",
        "dignity",
        "dignity_why",
        "functional",
        "benefic",
        "aspects_hitting",
        "aspects_hitting_disputed",
        "navamsa_sign",
        "shadbala_rupas",
        "shadbala_band",
    }
    assert len(payload["planets"]) == len(ve.VEDIC_PLANETS)
    for p in payload["planets"]:
        assert set(p) == required, f"{p['name']} field set drifted"


def test_planet_ids_are_lowercase_and_unique(payload: dict) -> None:
    ids = [p["id"] for p in payload["planets"]]
    assert ids == [i.lower() for i in ids]
    assert len(ids) == len(set(ids))


def test_aspects_hitting_are_valid_houses(payload: dict) -> None:
    for p in payload["planets"]:
        for house in p["aspects_hitting"] + p["aspects_hitting_disputed"]:
            assert 1 <= house <= 12
        # A planet never aspects via both lists at once.
        assert not set(p["aspects_hitting"]) & set(p["aspects_hitting_disputed"])


def test_nodal_aspects_are_the_disputed_ones(payload: dict) -> None:
    for p in payload["planets"]:
        if p["name"] in ("Rahu", "Ketu"):
            assert p["aspects_hitting"] == []
            assert p["aspects_hitting_disputed"], "nodes should still be shown"
        else:
            assert p["aspects_hitting_disputed"] == []


def test_mars_drishti_is_parashari(payload: dict) -> None:
    """Mars in the 11th must aspect the 2nd, 5th and 6th (its 4th, 7th, 8th)."""
    mars = next(p for p in payload["planets"] if p["id"] == "mars")
    assert mars["house_index"] == 11
    assert sorted(mars["aspects_hitting"]) == [2, 5, 6]


def test_sandhi_flags_only_sign_edges(payload: dict) -> None:
    for p in payload["planets"]:
        edge = p["degree"] < ac.SANDHI_ORB or p["degree"] > 30 - ac.SANDHI_ORB
        assert p["sandhi"] is edge


def test_nodes_carry_no_shadbala(payload: dict) -> None:
    for p in payload["planets"]:
        if p["name"] in ("Rahu", "Ketu"):
            assert p["shadbala_rupas"] is None
        else:
            assert isinstance(p["shadbala_rupas"], float)


def test_houses_are_complete_and_ordered(payload: dict) -> None:
    houses = payload["houses"]
    assert [h["house"] for h in houses] == list(range(1, 13))
    assert sum(h["sarvashtakavarga"] for h in houses) == 337


def test_dasha_children_tile_their_parent(payload: dict) -> None:
    for maha in payload["dashas"]["timeline"]:
        children = maha["children"]
        assert children, "every mahadasha carries its antardashas"
        assert len(children) == 9
        assert children[0]["from_jd"] == pytest.approx(maha["from_jd"], abs=0.01)
        assert children[-1]["to_jd"] == pytest.approx(maha["to_jd"], abs=0.01)
        for a, b in pairwise(children):
            assert a["to_jd"] == pytest.approx(b["from_jd"], abs=0.01)


def test_exactly_one_active_mahadasha(payload: dict) -> None:
    active = [m for m in payload["dashas"]["timeline"] if m["status"] == "active"]
    assert len(active) == 1
    assert active[0]["lord"] == payload["dashas"]["current"]["mahadasha"]


def test_findings_and_withheld_partition_the_houses(payload: dict) -> None:
    seen = {f["house"] for f in payload["findings"]} | {w["house"] for w in payload["withheld"]}
    assert seen == set(range(1, 13))


def test_citations_resolve_into_the_evidence_list(payload: dict) -> None:
    known = {e["id"] for e in payload["evidence"]}
    for f in payload["findings"]:
        assert f["citations"], "a finding without citations cannot be audited"
        for cid in f["citations"]:
            assert cid in known


def test_gate_travels_with_the_payload(payload: dict) -> None:
    assert payload["gate"]["minimum_agreeing_kinds"] >= 2
    assert "distinct kinds of factor" in payload["gate"]["rule"]


def test_meta_declares_sidereal_and_no_storage(payload: dict) -> None:
    assert payload["chart_meta"]["zodiac"] == "sidereal"
    assert "Lahiri" in payload["chart_meta"]["ayanamsa"]
    assert "not stored" in payload["disclaimer"]


# ── vargas ────────────────────────────────────────────────────────────


def test_all_sixteen_vargas_are_exposed(payload: dict) -> None:
    codes = [v["code"] for v in payload["vargas"]]
    assert len(codes) == 16
    assert codes[0] == "D1" and codes[-1] == "D60"
    assert len(set(codes)) == 16


def test_each_varga_is_complete(payload: dict) -> None:
    for v in payload["vargas"]:
        assert v["name"] and v["read_for"]
        assert v["ascendant_sign"] in ve.SIGNS
        assert len(v["positions"]) == len(ve.VEDIC_PLANETS)
        for pos in v["positions"]:
            assert 1 <= pos["house"] <= 12
            assert pos["sign"] in ve.SIGNS
            assert isinstance(pos["vargottama"], bool)


def test_d1_matches_the_rasi_and_is_never_vargottama(payload: dict) -> None:
    d1 = next(v for v in payload["vargas"] if v["code"] == "D1")
    assert d1["ascendant_sign"] == payload["ascendant"]["sign"] == "Aries"
    by_name = {p["name"]: p for p in payload["planets"]}
    for pos in d1["positions"]:
        assert pos["sign"] == by_name[pos["name"]]["sign"]
        assert pos["house"] == by_name[pos["name"]]["house_index"]
        # D1 cannot be "vargottama with itself"; the flag would be vacuous.
        assert pos["vargottama"] is False


def test_vargottama_means_same_sign_as_d1(payload: dict) -> None:
    by_name = {p["name"]: p["sign"] for p in payload["planets"]}
    for v in payload["vargas"]:
        if v["code"] == "D1":
            continue
        for pos in v["positions"]:
            assert pos["vargottama"] == (pos["sign"] == by_name[pos["name"]])


# ── house dossiers ────────────────────────────────────────────────────


def test_every_house_carries_a_full_dossier(payload: dict) -> None:
    required = {
        "house",
        "sign",
        "sign_index",
        "topic",
        "governs",
        "lord",
        "lord_placement",
        "occupants",
        "aspects_received",
        "sarvashtakavarga",
        "sarvashtakavarga_band",
        "karaka",
        "karaka_note",
        "karaka_placement",
        "currently_active",
    }
    assert len(payload["houses"]) == 12
    for h in payload["houses"]:
        assert set(h) == required, f"house {h['house']} field set drifted"
        assert h["governs"], "a house must say what it governs"
        assert h["karaka_note"]
        assert h["lord_placement"]["dignity_why"]


def test_dossier_occupants_agree_with_the_planet_list(payload: dict) -> None:
    for h in payload["houses"]:
        expected = {p["name"] for p in payload["planets"] if p["house_index"] == h["house"]}
        assert {o["name"] for o in h["occupants"]} == expected


def test_dossier_aspects_agree_with_the_planet_list(payload: dict) -> None:
    for h in payload["houses"]:
        expected = {
            p["name"]
            for p in payload["planets"]
            if h["house"] in p["aspects_hitting"] + p["aspects_hitting_disputed"]
        }
        assert {a["planet"] for a in h["aspects_received"]} == expected


def test_sav_band_matches_the_thresholds(payload: dict) -> None:
    for h in payload["houses"]:
        pts, band = h["sarvashtakavarga"], h["sarvashtakavarga_band"]
        if band == "well supplied":
            assert pts >= 30
        elif band == "thinly supplied":
            assert pts <= 25
        else:
            assert 25 < pts < 30


def test_currently_active_only_names_running_dasha_lords(payload: dict) -> None:
    running = {
        payload["dashas"]["current"]["mahadasha"],
        payload["dashas"]["current"]["antardasha"],
    }
    for h in payload["houses"]:
        for line in h["currently_active"]:
            assert any(lord and lord in line for lord in running), line


# ── compatibility payload ─────────────────────────────────────────────

TRIO = [
    {
        "label": "Epoch A",
        "year": 2000,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 51.5074,
        "lon": -0.1278,
        "tz": 0.0,
        "place": "London, UK",
    },
    {
        "label": "Epoch B",
        "year": 2010,
        "month": 6,
        "day": 21,
        "hour": 6,
        "minute": 0,
        "lat": 22.7196,
        "lon": 75.8577,
        "tz": 5.5,
        "place": "Indore, India",
    },
    {
        "label": "Epoch C",
        "year": 1995,
        "month": 3,
        "day": 21,
        "hour": 18,
        "minute": 0,
        "lat": 28.6139,
        "lon": 77.2090,
        "tz": 5.5,
        "place": "Delhi, India",
    },
]


def test_two_people_give_one_pair(pinned_now) -> None:
    out = ac.build_compatibility_payload(TRIO[:2], mode="relationship", now=pinned_now)
    assert len(out["pairs"]) == 1
    assert out["pairs"][0]["milan"]["maximum"] == 36.0


def test_three_people_give_three_pairs(pinned_now) -> None:
    out = ac.build_compatibility_payload(TRIO, mode="friendship", now=pinned_now)
    assert len(out["pairs"]) == 3
    assert {frozenset((p["a"], p["b"])) for p in out["pairs"]} == {
        frozenset(("Epoch A", "Epoch B")),
        frozenset(("Epoch A", "Epoch C")),
        frozenset(("Epoch B", "Epoch C")),
    }


def test_compatibility_payload_is_serialisable_and_complete(pinned_now) -> None:
    out = ac.build_compatibility_payload(TRIO, mode="relationship", now=pinned_now)
    assert json.loads(json.dumps(out))
    for pair in out["pairs"]:
        assert set(pair) >= {
            "a",
            "b",
            "mode",
            "findings",
            "withheld",
            "milan",
            "doshas",
            "overlays",
            "cross_aspects",
            "dasha_sync",
            "evidence",
            "navamsa_note",
        }
        for f in pair["findings"]:
            assert f["topic"] and f["verdict"] and f["kinds"]
        assert pair["milan"]["critique"]
        assert len(pair["overlays"]["a_into_b"]) == len(ve.VEDIC_PLANETS)


def test_friendship_mode_drops_the_marriage_kootas(pinned_now) -> None:
    out = ac.build_compatibility_payload(TRIO[:2], mode="friendship", now=pinned_now)
    names = {k["name"] for k in out["pairs"][0]["milan"]["kootas"]}
    assert not ({"Yoni", "Nadi", "Varna"} & names)


def test_compatibility_carries_the_framing_note(pinned_now) -> None:
    out = ac.build_compatibility_payload(TRIO[:2], now=pinned_now)
    assert "not a disqualification" in out["disclaimer"]
    assert "birth caste" in out["disclaimer"]
