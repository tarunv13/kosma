# Changelog

All notable changes to KOSMA will be documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — divisions, comparison, and house detail

- **All sixteen divisional charts in the client.** A D1–D60 selector redraws
  the same South Indian grid for any varga, showing each division's name, what
  it is read for, its own ascendant, and a **vargottama** marker on any graha
  holding the same sign as in D1. Drishti tracing stays D1-only and says so:
  aspects are computed in the rasi, and painting rasi aspects over a D9 grid
  would assert something never calculated.
- **House dossiers.** Every finding expands into the full structure of its
  bhava — what the house governs, the sign on it, its lord and where that lord
  went with its dignity reasoning, occupants with degrees and nakshatras,
  benefic and malefic drishti separated, sarvashtakavarga with its band, the
  natural karaka and its placement, and whether a running dasha lord rules or
  occupies it. **Withheld houses get a dossier too** — the gate refuses a
  verdict, not the facts.
- **Bhava karakas and house significations** (`interpretations.BHAVA_KARAKA`,
  `BHAVA_KARAKA_NOTE`, `HOUSE_GOVERNS`). The 10th is flagged as having the
  least settled karaka of the twelve rather than picking one silently.
- **`POST /api/compatibility`** and a `/compare` page: two or three charts,
  relationship or friendship mode, tabbed per pair into Findings, kootas with
  doshas, Synastry, and the evidence ledger. Findings lead; the score sits
  beneath with its critique.
- Contract bumped to **1.1** (additive — `vargas` plus the enriched `houses`).
  `tests/test_api_contract.py` caught the shape change on the first run, which
  is what it is for.

### Changed — Ethereal Light overhaul

- **Light theme throughout.** Warm off-white paper (`#FAF9F6`), deep navy ink
  (`#0A1128`), vellum panels with hairlines rather than frosted glass — glass
  over a light ground reads as grey mud. Every accent darkened until it holds
  contrast: text gold is `#8A5D0F`, with bright gold surviving only as a fill.
- **Wider shell.** 92% of viewport capped at 1400px, laid out as a
  twelve-column grid at `xl` — chart on five, findings on seven, timeline and
  yogas full width. Previously a narrow centre column.
- **Type scale rebuilt.** 16px base, nothing functional under 12px,
  `text-rendering: optimizeLegibility` and grayscale antialiasing global,
  tabular numerals on every figure.
- **Background is now an engraved orrery in SVG**, not a WebGL starfield:
  astrolabe graticule with twelve sign divisions and five-degree limb ticks,
  counter-rotating orbital ellipses, and planet motes, all under 12% opacity
  with pointer parallax at three depths.

### Removed

- `three`, `@react-three/fiber`, `@types/three` (18 packages). WebGL cannot
  draw a crisp hairline — `lineWidth` is capped at one device pixel in every
  major implementation — so the fine-line brief was better served by SVG,
  which also prints and costs nothing to composite.

### Added — Living Cosmos frontend

- **`web/`** — a React 19 / Next.js 15 client, Playfair Display for headings
  and JetBrains Mono for every figure. (Shipped first as a dark glassmorphic
  surface; see the Ethereal Light overhaul above for the palette it landed on.)
- **`<VedicChartEngine />`** — South Indian rasi chart with fixed sign cells.
  Clicking a graha draws its drishti as curved bezier rays (d3-shape
  `curveBasis` through a centre-pulled control point, animated on
  `pathLength`) and dims every house the aspect does not touch. Retrograde is
  red, sandhi carries a purple marker, sarvashtakavarga sits quietly in each
  cell. Nodal aspects render dashed, because BPHS does not grant them.
- **`<DashaTimeline />`** — a horizontal Time River where period widths are
  proportional to real duration; opening a mahadasha reveals its antardashas at
  the same scale.
- **`<CosmicCard />`** — yogas as artifacts, gold for auspicious and dim blue
  for challenging, each carrying its classical rule and source. Opening an
  upaya triggers a particle burst and washes the yoga's houses on the chart.
- **`<EvidencePanel />`** — findings with confidence and expandable citations,
  and withheld topics at equal visual weight.
- **`POST /api/chart`** and **`kosma/api_contract.py`** — a versioned wire
  contract, deliberately narrower than the grounding pack. `src/types/chart.ts`
  mirrors it field for field, and `tests/test_api_contract.py` asserts the
  field set so a rename on one side is a red build rather than an `undefined`
  on screen. The client refuses to render on a major-version mismatch.
- Narrow CORS: explicit origin allowlist (never a wildcard), credentials off,
  configurable via `KOSMA_CORS_ORIGINS`, defaulting to localhost development.

### Notes on the frontend's limits

- Remedies attach to **grahas, never to yogas**. There is a classical register
  per planet; there is no canonical remedy per combination, so none is
  invented. Gemstones carry the loudest caveat.
- Nothing is framed as unlocked or earned. The visual language is generous;
  the claims underneath are unchanged.
- No component library and no build-time asset pipeline beyond Next itself;
  the celestial field is hand-written SVG.

### Fixed (frontend)

- A fixed background layer at a negative z-index is painted over by the body's
  own background box. The opaque ground now lives on `<html>` only.
- The retrograde mark collided with the degree on two-letter glyphs.

### Added

- **Compatibility engine** (`kosma/compatibility.py`) for two or three charts,
  in two modes because they are different questions:
  - `relationship` — the full Ashtakoota (guna milan) out of 36.
  - `friendship` — the same machinery with Yoni and Nadi dropped, since those
    exist to assess sexual and genetic compatibility and say nothing about a
    friendship, and Varna dropped as directional and marriage-shaped. The
    remaining tally is labelled as KOSMA's construction from classical parts,
    not as a classical named scheme.
- **Dosha checks with their cancellations** — mangal (kuja) including the
  mutual-cancellation rule, bhakoot, and nadi. Cancellation conditions are
  routinely omitted by people quoting a dosha, so they are computed and shown
  alongside.
- **Synastry** — house overlays in both directions, cross-chart drishti onto
  each other's ascendant, Moon, Venus and Sun, D9 ascendant relationship, and
  a comparison of the dashas both people are actually running.
- Three people are compared **pairwise**. There is no classical method for
  scoring a group as a whole and inventing one would contradict the rest of
  this codebase.
- **`GET` / `POST /compatibility`** with an HTML result, and a `_layout.html`
  base template shared across pages.

### Changed

- **Redesigned the interface** as a precision instrument: near-black ground,
  hairline rules, tabular numerals throughout, a single amber accent with
  signal colour reserved for actual signal. Proportion bars are drawn with
  block characters because the CSP forbids inline styles and therefore
  server-set widths — which suits the look and costs nothing.
- Compatibility results **lead with the gated findings**, not the score.
  Ashtakoota weighs eight Moon-derived factors and ignores both ascendants,
  the 7th lord, Venus, Mars and the dashas, so it is reported as one input
  with its critique attached.
- Extracted the confirmation rule into `evidence.run_gate()`, so the natal and
  compatibility layers share one implementation rather than a copy.
- Form errors on the compatibility route render as an HTML page instead of raw
  JSON, and name the failing block by position rather than by the name typed
  into it.

### Fixed

- Inputs carrying only a `list` attribute have no `type` in the markup and
  were missing every form rule, because the stylesheet matched
  `input[type="text"]`. Matched by exclusion instead.
- Score cells could wrap mid-figure ("0 /" then "1").

### Notes

- Varna is computed because it is one of the eight, and is labelled in the
  data, the UI and the docs as a classification by the Moon sign's element —
  not anyone's birth caste, and not a statement about social standing.

## [0.3.0] - 2026-08-08

The release that turns KOSMA from a chart generator into a grounding layer for
AI interpretation. The organising principle: **the ephemeris computes, the
model interprets, and neither does the other's job.**

### Added

- **Evidence ledger and confirmation gate** (`kosma/evidence.py`). Every
  observation is recorded as a typed, sourced item across nine factor kinds
  (house lord placement, dignity, conjunction, aspect, nakshatra lord, yoga,
  dasha, transit, ashtakavarga). A topic is reported only when at least two
  *different* kinds of factor agree; each kind resolves to its own net first,
  so a kind that cancels itself out casts no vote. Topics below the line go to
  a `withheld` list with the reason attached, and the interpretation layer is
  forbidden from discussing them. Disputed material is displayed but never
  counted.
- **Grounding pack** (`kosma/grounding.py`) — one JSON object carrying every
  computed position, dignity, yoga, dasha date, transit window and piece of
  evidence, plus an explicit `constraints` list.
- **System prompt** (`prompts/system_prompt.md`) binding an interpreting model
  to the pack: no calculating, no inventing yogas, no discussing withheld
  topics, cite the evidence ids.
- **Dignity and strength** (`kosma/dignity.py`) — exaltation with exact
  degrees, moolatrikona, own sign, naisargika and tatkalika relations
  compounded to panchadha maitri, combustion orbs, dig bala, planetary war,
  and functional nature including a correct yogakaraka rule.
- **Aspects and chains** (`kosma/aspects.py`) — Parashari graha drishti with
  special aspects, Jaimini rashi drishti, conjunctions, dispositor and
  nakshatra-lord chains for Nadi-style reading.
- **Yoga detection** (`kosma/yogas.py`) — Raja, Yogakaraka, Dhana, Vipreeta
  (Harsha/Sarala/Vimala), Neechabhanga, Parivartana (Maha/Dainya/Khala),
  Pancha Mahapurusha, Gajakesari, Budhaditya, Chandra-Mangala, Adhi, Shakata,
  Sunapha/Anapha/Durudhara/Kemadruma, and Kala Sarpa. Each carries its rule
  and its source text. Kala Sarpa is emitted flagged, with its absence from
  the classical corpus stated.
- **Full varga engine** (`kosma/vargas.py`) — D1 through D60 including the
  unequal Trimsamsa, plus vargottama and a saptavarga dignity tally.
- **Ashtakavarga** (`kosma/ashtakavarga.py`) — Bhinna and Sarva, with the BPHS
  row totals asserted in the test suite.
- **Shadbala** (`kosma/shadbala.py`) — sthana, dig, kala, cheshta, naisargika
  and drik, with every omitted sub-component declared on the result rather
  than silently padded.
- **KP significators** (`kosma/kp.py`) — Placidus cuspal chains, the four-fold
  ABCD significator table, house significators, and ruling planets.
- **Transits and timing** (`kosma/transits.py`) — sign ingresses found by
  bisecting the ephemeris, sade sati with real window dates, and dasha x
  transit activation windows computed as interval intersections.
- **Nakshatra knowledge table** (`kosma/nakshatras.py`) — deity, symbol, gana,
  yoni, temperament, pada lord and signification for all 27, with contested
  fields flagged.
- **Client-held encrypted memory** (`kosma/memory.py`, optional extra
  `kosma[memory]`) — longitudinal continuity in a file the user holds,
  encrypted with a scrypt-derived key. The server never sees the file or the
  passphrase.
- **CLI** — `python -m kosma` emitting `json`, `prompt`, `bundle`, `report`,
  or `pdf`.
- **`POST /api/grounding`** returning the pack as JSON, under the same
  stateless, no-logging, rate-limited posture as the PDF route.
- **PDF sections** for yogas, strength, the evidence ledger, withheld topics,
  and activation windows.
- Test suite grown from 57 to 189 tests.

### Changed

- `Chart` now carries its own latitude, longitude and timezone offset, so
  strength and transit code no longer needs the location passed twice.
- `vedic_engine.antardasha_sequence()` enumerates antardashas over a window.

### Fixed

- The yogakaraka rule counted the lagna as a trikona, which made a yogakaraka
  of any lagna lord that also held a kendra. Restricted to the 5th and 9th,
  which reproduces exactly the six classical yogakarakas.
- `aspects.mutual_aspects()` shadowed a loop variable, conflating an `Aspect`
  with a planet name.

### Security

- Bumped `python-multipart` 0.0.29 -> 0.0.31, clearing PYSEC-2026-3036,
  PYSEC-2026-3037 and PYSEC-2026-3040. This release adds a second
  form-parsing endpoint, so the multipart parser is now on two paths.

### Notes

- **CI:** dropped the invalid `--disable-pip` flag from the `pip-audit` step
  so the dependency audit job actually runs.
- **One-click deploy:** `render.yaml` (Render Blueprint), `fly.toml` (Fly.io),
  and a `Procfile` for Heroku-style platforms. All three run uvicorn with
  `--no-access-log` and `--proxy-headers --forwarded-allow-ips=*`.
- `Makefile` with `install / dev / fmt / lint / type / test / smoke / audit /
   ci / docker / run / sample / clean` targets.
- `scripts/generate_sample.py` and `docs/sample-blueprint.pdf` — a real,
  regenerable example report so anyone landing on the README can see the
  output without running the app. Pinned to a fixed `today` so the file is
  stable in git diffs.
- SVG favicon (`kosma/static/favicon.svg`), linked from the form.

## [0.2.0] - 2026-05-25

### Added

- Renamed the project to **KOSMA** with a refreshed cover, wordmark, and
  five-letter brand identity.
- Circular sidereal chart wheel embedded in the PDF (12 sign sectors,
  whole-sign houses from the natal ascendant, planets at exact longitude,
  ascendant marker line).
- D9 Navamsa computation (`kosma.vedic_engine.navamsa_chart`) and a D9
  table in the PDF report.
- `/version` endpoint returning app name and semantic version.
- Modern Python packaging via `pyproject.toml` with `ruff`, `mypy`, and
  `pytest` configuration baked in.
- Real `pytest` test suite covering the engine, KP sub-divisions,
  Vimshottari dasha, panchanga, navamsa, and the HTTP layer.
- GitHub Actions CI: lint (ruff), type-check (mypy), tests (pytest), and
  dependency vulnerability scan (pip-audit) on every push and pull request.
- Multi-stage `Dockerfile` running as a non-root user with a healthcheck.
- `pre-commit` config, `.editorconfig`, `.dockerignore`.
- `LICENSE` (MIT), `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  this `CHANGELOG.md`.
- Issue and pull request templates under `.github/`.
- Dependabot config for `pip` and `github-actions`.

### Changed

- Restyled landing page to a darker cosmic Gen-Z aesthetic with a starfield
  hero, gradient wordmark, and gradient CTA.
- Internal package directory renamed `app/` -> `kosma/`.
- Smoke scripts updated to import from `kosma`.

## [0.1.0] - 2026-05-25

### Added

- Initial release as MyAstrologer: FastAPI form, in-memory PDF generation,
  Swiss Ephemeris engine with KP and Jaimini, embedded city table,
  rate limiting, security headers.
