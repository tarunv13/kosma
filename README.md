<div align="center">

# KOSMA

**Your sky, your story.**

A privacy-first Vedic astrology engine that computes a chart to arc-second precision, decides what that chart can actually support, and hands the result to an AI that is structurally unable to invent the rest.

[![CI](https://github.com/tarunv13/kosma/actions/workflows/ci.yml/badge.svg)](https://github.com/tarunv13/kosma/actions/workflows/ci.yml)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/tarunv13/kosma)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-262626.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Privacy: no storage](https://img.shields.io/badge/privacy-no%20storage-7c3aed)](#privacy-and-security)

</div>

---

## What you get

A multi-page PDF with:

- **Cover** with a clean wordmark, your name, and birth coordinates.
- **Birth snapshot** — ascendant degree, nakshatra, KP star/sub/sub-sub chain, lagna lord, Lahiri ayanamsa.
- **Circular sidereal chart wheel** (12 sign sectors, whole-sign houses from the natal lagna, planets at exact longitude, ascendant marker).
- **Planetary positions table** — sign, exact degree (DMS), nakshatra & pada, KP chain, house, retrograde flag.
- **Jaimini chara karakas** (Atmakaraka -> Darakaraka).
- **D9 Navamsa** placements for every body, with houses derived from the D9 ascendant.
- **Panchanga at birth** — vara, tithi & paksha, yoga, karana, Moon's nakshatra & pada, Sun-Moon arc.
- **Vimshottari dasha timeline** — past, current, and upcoming mahadashas with the active period highlighted, plus the live mahadasha / antardasha / pratyantar elapsed percentages.
- **Yogas formed** — each with the rule that produced it and the text it comes from. If a yoga is absent, it did not form; the list is not abridged.
- **Strength** — six-fold Shadbala per graha and Sarvashtakavarga per house.
- **Evidence ledger** — every observation the engine made, with its arithmetic and its citation, so any line can be audited.
- **Withheld topics** — areas of life the chart cannot support a reading of, listed as such rather than filled in.
- **Activation windows** — where the running dasha and a slow transit converge, dated from bisected ephemeris ingresses.
- **Soul Blueprint** sections — Ascendant, Lagna lord, all nine planets, Atmakaraka, Darakaraka.
- **Privacy notice and disclaimer.**

All numbers come from Swiss Ephemeris with Lahiri (Chitrapaksha) ayanamsa, the Indian Vedic standard.

> See [`docs/sample-blueprint.pdf`](docs/sample-blueprint.pdf) for a real
> generated report — the v1.0 reference chart, regenerable with `make sample`.

## AI interpretation without the invention

Ask a language model to read a birth chart and it will produce fluent,
confident text in which the houses are wrong, the dasha dates are wrong, and a
yoga that does not exist is described in detail. A better prompt does not fix
this, because a prompt is a request the model can decline.

KOSMA fixes it structurally, along the split Jyotisha already has between
*ganita* (calculation) and *phalita* (interpretation):

**The ephemeris computes. The model interprets. Neither does the other's job.**

Every position, dignity, aspect, yoga, varga, ashtakavarga point, shadbala
figure, dasha date and transit window is resolved before a model sees anything.
Then a **confirmation gate** decides what may be said at all: an area of life is
reported only when at least two *different* kinds of chart factor agree about
it, out of nine kinds tracked. Each kind resolves to its own net first, so a
kind that cancels itself out casts no vote, and disputed material never counts.
What fails the test is not softened into a hedge — it is listed as **withheld**,
and the shipped system prompt forbids the model from discussing it.

```bash
# a readable structural summary — no interpretation, just what the chart holds
python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK" --format report

# the grounding pack, for your own tooling
python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK" --format json

# prompt + pack, ready to paste into a Claude Project or an API call
python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK" --format bundle
```

Or over HTTP: `POST /api/grounding` returns the same pack as JSON, under the
same stateless, no-logging posture as the PDF route.

For a Claude Project: `prompts/system_prompt.md` goes in the project
instructions, the pack goes in project knowledge. The model then has no reason
to calculate and no room to invent.

> [`docs/architecture.md`](docs/architecture.md) explains the design in full —
> including what it deliberately does **not** solve.

## Two front ends

| | Server-rendered (`kosma/templates/`) | Living Cosmos (`web/`) |
|---|---|---|
| Stack | FastAPI + Jinja, no JS framework | Next.js 15 / React 19 |
| Look | Precision instrument — dark, hairline rules, tabular numerals | Ethereal Light — off-white paper, deep navy ink, engraved SVG orrery |
| Output | PDF + HTML compatibility report | Interactive chart, drishti rays, dasha river, yoga cards |
| Needs JS | No | Yes |

Both read the same engine and obey the same gate. The server-rendered path is
the privacy-maximal fallback: no framework, no build step, and a
`default-src 'self'` policy with no inline anything.

```bash
# terminal 1 — the engine
uvicorn kosma.main:app --port 8000
# terminal 2 — the client
cd web && npm install && npm run dev     # http://localhost:3000
```

The client talks to `POST /api/chart`, a **versioned wire contract**
(`kosma/api_contract.py`) mirrored field for field by `web/src/types/chart.ts`.
`tests/test_api_contract.py` asserts the field set, so renaming a field on one
side is a red build rather than an `undefined` on screen — and the client
refuses to render at all on a major-version mismatch.

The interactive client keeps the same discipline under a much more generous
surface: withheld topics render at full visual weight with their reasons, every
finding shows its confidence and expandable citations, yoga cards always carry
the rule and the source text, and remedies attach to **grahas rather than
yogas** because no canonical per-yoga remedy exists to attach. See
[`web/README.md`](web/README.md).

## Compatibility

Two or three charts, at `/compatibility`, in two modes — because they are
different questions and deserve different factors.

| | Relationship | Friendship |
|---|---|---|
| Tally | Ashtakoota, 36 points | Affinity factors only |
| Kootas | all eight | Yoni, Nadi and Varna dropped |
| Topics | rapport, attraction, communication, direction, friction, durability | rapport, communication, direction, **mutual gain**, friction, durability |

Yoni and Nadi exist to assess sexual and genetic compatibility. They have
nothing to say about a friendship, so friendship mode does not compute them
rather than computing them and asking you to ignore them. What remains is
labelled as this project's construction from classical parts, not as a
classical named scheme.

Alongside the tally: **doshas with their cancellations** (mangal including the
mutual-cancellation rule, bhakoot, nadi), **synastry** (house overlays both
ways, cross-chart drishti, D9 ascendant relationship), and a comparison of the
**dashas both people are actually running**. Three people are compared
pairwise — there is no classical method for scoring a group as a whole, and
inventing one would contradict everything else here.

**The findings lead; the score does not.** Ashtakoota weighs eight Moon-derived
factors and ignores both ascendants, the 7th house and its lord, Venus, Mars,
and the dashas in force. It is reported as one input among several with its
critique attached, underneath the topics that cleared the same confirmation
gate the natal engine uses.

Two things are named plainly in the product, not buried:

- **Varna** here is a classification by the Moon sign's element — a temperament
  class assigned by the sky. It is not anyone's birth caste and carries no
  statement about social standing. Its rule is also directional and gendered in
  origin; KOSMA assumes no genders, so both directions are shown.
- **Nadi** and **Bhakoot** doshas are routinely used to refuse matches, usually
  without the classical cancellation conditions that go with them. Those
  conditions are computed and reported. A dosha is a flag to examine, not a
  disqualification of a person.

### What the engine computes

| Layer | Module | Covers |
|---|---|---|
| Positions | `vedic_engine.py` | Sidereal longitudes, nakshatra & pada, KP star/sub/sub-sub, Vimshottari, panchanga |
| Dignity | `dignity.py` | Exaltation with exact degrees, moolatrikona, panchadha maitri, combustion, dig bala, graha yuddha, functional nature |
| Geometry | `aspects.py` | Graha drishti with special aspects, Jaimini rashi drishti, conjunctions, dispositor & nakshatra chains |
| Yogas | `yogas.py` | Raja, Yogakaraka, Dhana, Vipreeta, Neechabhanga, Parivartana, Pancha Mahapurusha, Gajakesari, Budhaditya, Chandra-Mangala, Adhi, Shakata, the lunar set, Kala Sarpa (flagged) |
| Divisions | `vargas.py` | D1–D60 including the unequal Trimsamsa, vargottama, saptavarga tally |
| Strength | `ashtakavarga.py`, `shadbala.py` | Bhinna & Sarva; sthana, dig, kala, cheshta, naisargika, drik |
| KP | `kp.py` | Placidus cuspal chains, ABCD significators, house significators, ruling planets |
| Timing | `transits.py` | Bisected sign ingresses, sade sati, dasha × transit activation windows |
| Nakshatras | `nakshatras.py` | Deity, symbol, gana, yoni, temperament, pada lord for all 27 |
| Judgement | `evidence.py` | The ledger and the confirmation gate |
| Compatibility | `compatibility.py` | Ashtakoota, doshas with cancellations, synastry, dasha sync |

Calculation coverage was shaped by two prior libraries:
[jyotishganit](https://github.com/northtara/jyotishganit) for the varga,
shadbala and ashtakavarga surface and the single serialisable chart object, and
[VedicAstro](https://github.com/diliprk/VedicAstro) for the KP significator
model and cusp-based houses kept distinct from sign-based ones.

## How it works

```
 [browser form]  --POST /generate------+
 [CLI / your code] --POST /api/grounding--+
                                          |
                     in-memory only:      v
                       build_chart()  ->  dignity, aspects, yogas
                                      ->  vargas D1-D60, ashtakavarga, shadbala
                                      ->  KP significators, dasha, gochar
                                          |
                                          v
                            evidence ledger + confirmation gate
                              (topics without two agreeing
                               kinds of factor are WITHHELD)
                                          |
                        +-----------------+-----------------+
                        v                                   v
                  render PDF (BytesIO)              grounding pack (JSON)
                        |                                   |
                        v                                   v
                  [PDF download]                    [model interprets,
                                                     cannot recalculate]
```

Nothing on this path touches the disk. The server is stateless.

## Run locally

Requires Python 3.11 or newer.

```bash
# Editable install with dev tooling
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run the dev server
uvicorn kosma.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>.

## Run with Docker

```bash
docker build -t kosma .
docker run --rm -p 8000:8000 kosma
```

The container runs as a non-root user, exposes a `/healthz` HTTP healthcheck, and starts uvicorn with `--no-access-log` so the platform never sees per-request lines.

## One-click deploy

KOSMA ships ready-to-deploy configs for popular Python platforms.

| Platform | File | How |
|---|---|---|
| **Render** | `render.yaml` | Fork on GitHub, then in Render: *New +* -> *Blueprint* -> point at the fork. Render reads the file and provisions a free web service with `/healthz` checks. |
| **Fly.io** | `fly.toml` | `fly launch --copy-config` from the repo root. Builds via `Dockerfile`, single shared-CPU VM, auto-stop when idle. |
| **Heroku-style PaaS** | `Procfile` | Any platform that reads `Procfile` (Heroku, Dokku, Coolify) starts uvicorn with the right flags. |
| **Anything Docker-shaped** | `Dockerfile` | Build, tag, push to your registry; deploy. |

> All four configs run uvicorn with `--no-access-log` and `--proxy-headers --forwarded-allow-ips=*` so the rate limiter sees real client IPs through any reverse proxy.

## Quality gates

```bash
make ci             # run everything CI runs locally (lint, type, test, audit, smoke)

# or individually:
ruff check .                    # lint
ruff format --check .           # format
mypy kosma                      # type check
pytest                          # 225 tests
pytest --cov=kosma              # with coverage
pip-audit -r requirements.txt   # CVE scan

# end-to-end smoke checks
python scripts/smoke_test.py    # engine vs reference chart
python scripts/smoke_http.py    # HTTP layer in-process via TestClient
```

CI runs all of the above on every push and PR via `.github/workflows/ci.yml`, on Python 3.11 and 3.12.

## Project layout

```
.
├── kosma/                      The application package
│   ├── main.py                 FastAPI app: routes, validation, headers, rate limit
│   ├── cli.py                  python -m kosma: json / prompt / bundle / report / pdf
│   ├── vedic_engine.py         Swiss Ephemeris + KP chain + Jaimini + dasha + panchanga
│   ├── dignity.py              Dignity, panchadha maitri, combustion, functional nature
│   ├── aspects.py              Graha & rashi drishti, conjunctions, lordship chains
│   ├── yogas.py                Yoga detection from an explicit, sourced rule table
│   ├── vargas.py               Divisional charts D1-D60
│   ├── ashtakavarga.py         Bhinna + Sarva ashtakavarga
│   ├── shadbala.py             Six-fold strength, with omissions declared
│   ├── kp.py                   Placidus cusps, ABCD significators, ruling planets
│   ├── transits.py             Ingresses, sade sati, dasha x transit windows
│   ├── nakshatras.py           The 27 mansions as a knowledge table
│   ├── evidence.py             Evidence ledger + the confirmation gate
│   ├── compatibility.py        Ashtakoota, doshas, synastry, dasha sync
│   ├── grounding.py            The JSON grounding pack handed to a model
│   ├── memory.py               Client-held encrypted longitudinal memory
│   ├── interpretations.py      Classical interpretation lookups (signs, houses, dashas)
│   ├── pdf_generator.py        PDF builder + circular chart wheel
│   ├── cities.py               Embedded city -> (lat, lon, tz) lookup
│   ├── templates/              _layout, index, compatibility, result, error
│   └── static/                 One stylesheet, one small script, no build step
├── prompts/system_prompt.md    The interpretation-layer system prompt
├── docs/architecture.md        Why the system is shaped this way, and its limits
├── tests/                      pytest suite (225 tests)
├── scripts/                    smoke_test.py, smoke_http.py
├── .github/                    CI, Dependabot, issue/PR templates
├── Dockerfile                  Multi-stage, non-root, healthcheck
├── pyproject.toml              Project metadata + ruff/mypy/pytest config
├── requirements.txt            Pinned runtime deps (CVE-clean as of release)
├── .pre-commit-config.yaml     Local commit hooks
├── LICENSE                     MIT
├── SECURITY.md                 Vulnerability disclosure policy
├── CONTRIBUTING.md             Dev workflow + privacy/astro checklists
├── CODE_OF_CONDUCT.md          Contributor Covenant 2.1
├── CHANGELOG.md                Keep a Changelog format
└── README.md                   You are here
```

## Privacy and security

KOSMA is built on the assumption that birth data is sensitive.

| Concern | How KOSMA handles it |
|---|---|
| **Persistence of birth data** | None. The data is consumed inside one request handler, fed to the PDF generator, and gone when the response is written. No database, no file writes, no caching. |
| **Logs** | The app does not log form fields, request bodies, exception arguments, or any computed birth data. The Dockerfile runs uvicorn with `--no-access-log`. |
| **Third-party calls** | None. No geocoding API, no fonts loaded from a CDN, no analytics, no tracking pixels. The city table is embedded. |
| **Cookies and sessions** | None. The endpoint is a single POST that returns a PDF. |
| **Rate limiting** | `slowapi`, per-IP. 120 hits/hour on `GET /`, 10/hour on `POST /generate` and `POST /api/grounding`. |
| **Longitudinal memory** | Held by the user, never the server. `kosma/memory.py` writes a locally encrypted file (scrypt-derived key, Fernet AEAD); no endpoint accepts it and the passphrase never leaves the machine. A one-way chart fingerprint lets a file prove which chart it belongs to without carrying the birth details. Optional extra: `pip install "kosma[memory]"`. |
| **AI layer** | The grounding pack is computed and returned in one response; no chart data is sent to any model by this codebase. What you do with the pack is your choice, made explicitly. |
| **HTTP headers** | `Content-Security-Policy: default-src 'self'`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` blocks geolocation/camera/microphone/payment, `Cache-Control: no-store` on the form and the PDF. |
| **Server input validation** | Date / time / lat / lon / tz are validated. Out-of-range values return `400` with a clear message. Validation errors do not echo the input. |
| **API surface reduction** | `/docs`, `/redoc`, and `/openapi.json` are disabled. `<meta robots noindex,nofollow>` on the form page. |
| **Dependency security** | `pip-audit` runs in CI; Dependabot opens weekly PRs for `pip`, `github-actions`, and `docker` updates. The current dependency set is CVE-clean as of v0.2.0. |

What is **not** handled by the app and is your responsibility when deploying:

- **HTTPS**. Terminate TLS at your reverse proxy or platform. The app does not.
- **Access logs at the platform level**. Configure to disable or strip access logs if you treat IP addresses as personal data in your jurisdiction.
- **Edge-level DDoS protection**. Put the app behind your platform's edge or a CDN.

See [SECURITY.md](SECURITY.md) for the full threat model and how to report vulnerabilities.

## Astrological notes

- **Ayanamsa**: Lahiri (Chitrapaksha), the Indian Vedic standard.
- **Houses**: whole-sign houses, counted from the natal ascendant.
- **Node**: mean lunar node (`swe.MEAN_NODE`) for Rahu / Ketu.
- **D9 Navamsa**: Parashari rule with element-trine starting points (movable -> same sign, fixed -> 9th, dual -> 5th).
- **KP**: 9-fold sub-division of each nakshatra, then 9-fold sub-sub-division, both in Vimshottari dasha proportions.
- **Jaimini**: chara karakas ranked by descending degree-in-sign of the seven core planets; rashi drishti by modality.
- **Two house systems, both reported**: whole-sign everywhere, Placidus for KP (which is cusp-based). Each planet carries `house_whole_sign` and `house_placidus` rather than a single reconciled number that would be wrong for one system.
- **Contested points are flagged, not resolved**: the nodes' exaltation, nodal aspects, the victor of a graha yuddha, D60 counting in even signs, purushartha assignment, and Kala Sarpa's provenance. These are emitted with a `disputed` marker and never count as evidence.
- **Shadbala is partial and says so**: varsha, masa and yuddha bala are not computed, so totals should not be read against the classical minimum thresholds as though complete.
- **Birth-time accuracy** matters. The ascendant changes sign every two hours, and a ten-minute drift can shift the nakshatra pada and several KP sub-divisions.
- **DST**: the embedded city table uses standard civil offsets. If a birth fell during a DST window, switch to manual coordinates and subtract one hour.

## Engine reference chart

The smoke tests pin the engine against the **J2000.0 epoch** — 1 January 2000, 12:00 UT, London (51.5074 N, 0.1278 W). A synthetic astronomical instant, deliberately: a public repository should not carry a real person's birth data, least of all one whose headline claim is that birth data is sensitive.

| | Computed by KOSMA | Independently verifiable in any Vedic software with Lahiri |
|---|---|---|
| Ascendant | Aries 0°09'40.9" | Same |
| Asc nakshatra / pada | Ashwini pada 1 | Same |
| KP chain (asc) | Ketu / Ketu / Venus | Same |
| Atmakaraka | Moon (Libra, H7) | Same |
| Darakaraka | Jupiter (Aries, H1) | Same |

The full chart is asserted in `tests/test_engine.py`. Adding tests for new charts means adding entries there.

## Disclaimer

KOSMA produces a tool for self-reflection. It is not medical, legal, financial, or psychological advice. For major life decisions, consult a qualified professional.

## License

MIT. See [LICENSE](LICENSE).
