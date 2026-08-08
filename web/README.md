# KOSMA web — the Living Cosmos client

A React 19 / Next.js 15 front end for the Python engine. An **Ethereal Light**
surface — warm off-white paper, deep navy ink, and a faint engraved orrery
behind everything — with the same epistemic rules as the rest of this
repository.

```bash
# terminal 1 — the engine
cd .. && uvicorn kosma.main:app --port 8000

# terminal 2 — the client
npm install
npm run dev          # http://localhost:3000
```

Next rewrites `/api/*` to `http://127.0.0.1:8000`, so the browser sees one
origin and CORS never comes into it. Point somewhere else with `KOSMA_API`.

## The stack, and why

| Choice | Reason |
|---|---|
| **Next.js 15 / React 19** | App Router, server components for the shell, client components only where interaction lives. |
| **SVG, not WebGL, for the background** | The brief calls for faint fine-line orbital rings. WebGL cannot draw a crisp hairline — `lineWidth` is capped at one device pixel everywhere and lines alias badly — so the celestial field is SVG. It stays sharp at any density, costs nothing to composite, and prints. This replaced an earlier R3F starfield and removed `three`, `@react-three/fiber` and `@types/three`. |
| **Zustand** | Hover and selection are separate slices from the chart object, so moving the cursor across the grid does not re-render the evidence panel. |
| **Framer Motion** | Drishti rays animate on `pathLength`; planets spring into place; every animation checks `useReducedMotion`. |
| **d3-shape** | `curveBasis` through a centre-pulled control point gives the bowed aspect rays. Only the shape module, not all of d3. |
| **Tailwind** | Design tokens live in `tailwind.config.ts` so the palette is declared once. |

## The contract

`src/types/chart.ts` mirrors `kosma/api_contract.py` field for field — the same
contract written twice, on purpose. `tests/test_api_contract.py` on the Python
side asserts the field set, so renaming a field there without renaming it here
is a red build rather than an `undefined` on screen.

The client checks the major version on every response and **refuses to render**
on a mismatch. A frontend quietly drawing fields whose meaning has changed is
exactly the failure this project exists to prevent, so it fails loudly instead.

## Layout and type

The shell runs to **92% of the viewport, capped at 1400px**, and becomes a
twelve-column grid at `xl`: chart on five columns, findings on seven, timeline
and yogas full width. Below `xl` it collapses to one column.

Base font size is **16px** with a deliberate scale in `tailwind.config.ts`;
nothing functional sits below 12px. `text-rendering: optimizeLegibility` and
grayscale antialiasing are set globally, and every figure is tabular so digits
do not jitter between renders.

## Colour carries meaning

Accents are darkened until they hold contrast on paper — bright gold
(`#FFD700`) is invisible on off-white, so text gold is `#8A5D0F` and the bright
tone survives only as a fill or a ring. Green is supported, red is under strain
or withheld, violet is contested or disputed. Nothing decorative is coloured.

## What you can look at

- **All sixteen divisions.** The D1–D60 selector redraws the grid for any
  varga, with vargottama marked. Drishti is offered in D1 only — aspects are
  computed in the rasi, so tracing them over a D9 grid would be asserting
  something the engine never calculated.
- **House dossiers.** Any finding expands into the full bhava: what it governs,
  its sign, its lord and where that lord went, occupants, drishti split benefic
  from malefic, ashtakavarga, the natural karaka, and whether a dasha lord is
  running through it. Withheld houses expand too — the gate refuses a verdict,
  not the facts.
- **Compare** (`/compare`): two or three charts, relationship or friendship
  mode, pairwise. Never averaged into a group score, because no classical
  method for one exists.

## Three states

- **Rest** — planets sit in their houses; the field breathes.
- **Focus** — clicking a graha draws its drishti as curved rays and dims every
  house the aspect does not touch. Nodal aspects render dashed and purple,
  because BPHS does not grant them.
- **Soothed** — opening an upaya washes the houses that yoga touches in purple.

## What the beauty is not allowed to do

The visual language here is generous. The claims underneath are not, and the
two are kept apart deliberately:

- **Withheld topics render at full visual weight**, in their own panel, with
  the reason. The gate's whole point is that "the chart does not show this" is
  a result — hiding it to keep the screen pretty would defeat the system.
- **Every finding shows its confidence and its citation ids**, expandable to
  the underlying evidence with sources.
- **Yoga cards always carry the classical rule and the text it comes from.** A
  yoga with no classical source (Kala Sarpa) renders dimmed and labelled rather
  than dropped.
- **Remedies attach to grahas, never to yogas.** There is a well-attested
  classical register per planet; there is no canonical "remedy for Gaja Kesari
  Yoga", so none is invented. See `src/lib/remedies.ts`.
- **Nothing is framed as unlocked or earned.** A chart is not an achievement,
  and engagement mechanics are what the practitioners this project listens to
  complain about most.

## Fonts and CSP

Playfair Display, JetBrains Mono and Inter come through `next/font/google`,
which downloads at **build** time and self-hosts the result. The running page
makes no third-party request, matching the Python app's `default-src 'self'`.
A build machine does need network access once.

## Scripts

```bash
npm run dev        # dev server
npm run build      # production build (also typechecks)
npm run typecheck  # tsc --noEmit
npm run lint       # next lint
```
