# Architecture: how KOSMA avoids inventing your chart

The failure mode this system exists to prevent is specific and well documented.
Ask a language model to read a birth chart and it will produce fluent,
confident, well-organised text in which the house placements are wrong, the
dasha dates are wrong, and a yoga that does not exist is described in
convincing detail. Practising astrologers who have tested this report the same
things over and over: *it gets my houses wrong*, *it fails at timing*, *it
misreads the chart image*, *it invents combinations*.

The instinct is to fix this with a better prompt. That does not work, because a
prompt is a request and the model is free to decline it. The fix has to be
architectural.

## The one structural decision

**The ephemeris computes. The model interprets. Neither does the other's job.**

This is not a modern software idea imported into astrology. Jyotisha has always
divided into *ganita* (calculation) and *phalita* (interpretation), and an
acharya handed a correctly cast kundali does not recast it. The split is native
to the discipline; the system just enforces it.

```
  birth date, time, place
            |
            v
  +---------------------------+
  |  ganita  (deterministic)  |    Swiss Ephemeris, Lahiri sidereal
  |                           |    dignity, aspects, yogas, vargas D1-D60,
  |  no language model here   |    ashtakavarga, shadbala, KP, dasha, gochar
  +---------------------------+
            |
            v
  +---------------------------+
  |  evidence ledger + gate   |    every observation typed, sourced, cited
  |                           |    topics below the threshold are WITHHELD
  +---------------------------+
            |
            v
      grounding pack (JSON)  ------> prompts/system_prompt.md
            |                        binds the model to the pack
            v
  +---------------------------+
  |  phalita (a model)        |    renders what survived into language
  |  cannot calculate         |    cites evidence ids; cannot discuss
  |  cannot add a yoga        |    withheld topics
  +---------------------------+
```

Everything below is a consequence of that diagram.

## The confirmation gate

The rule that field practitioners converge on is that a claim needs several
independent chart factors behind it. Written into a prompt, this is ignored.
Written into `kosma/evidence.py`, it is a constraint.

Nine factor kinds are collected for each house: house lord placement, dignity,
conjunction, aspect, nakshatra lord, yoga, dasha, transit, ashtakavarga. Each
observation becomes an `Evidence` item with a stable id, a statement, the
arithmetic or placement that licenses it, a classical citation, and a polarity.

Three details make the gate actually bite, and each was a bug before it was a
feature:

1. **The threshold is per direction, not per pile.** Counting mere presence
   passed all twelve houses on every chart, because every house always has a
   lord somewhere, a nakshatra chain, and an ashtakavarga score. What must
   clear the bar is *agreement*: two distinct kinds pointing the same way.

2. **Each kind votes once, on its own net.** Every house receives both benefic
   and malefic drishti, so treating each aspect as its own vote let "aspect"
   support both directions at once and everything came back "contested". A kind
   that cancels itself out is not evidence for anything.

3. **Disputed material never counts.** Nodal aspects, the nodes' exaltation,
   the victor of a graha yuddha, Kala Sarpa: all emitted, all visible, none of
   them able to push a topic over the line.

A topic that fails is not softened into a hedge. It is moved to `withheld` with
the reason, and the system prompt forbids the model from discussing it. On a
sample of five charts, four of sixty house-topics were withheld — the gate is
neither vacuous nor so strict that it says nothing.

**Withholding is a feature.** An acharya of fifty years says "the chart does
not clearly show this" more often than a novice, not less.

## Answering the field reports directly

| What practitioners report | What the architecture does |
|---|---|
| "It got my house placements wrong" | The model never places anything. Positions come from Swiss Ephemeris and are handed over resolved. |
| "It fails at prediction of event timing" | Ingress dates are found by bisecting the ephemeris to the minute; activation windows are literal interval intersections of dasha and transit. Nothing is estimated. |
| "It doesn't analyse the picture properly" | No image path exists. Input is date, time, place. |
| "It invents yogas" | `yogas.py` detects from an explicit rule table and the list is exhaustive. The prompt states that an absent yoga did not form. |
| "You have to feed it exact degree, nakshatra, pada, house" | That is precisely the grounding pack, generated automatically instead of assembled by hand. |
| "Upload the vimshottari table, then manually fix the dates" | Dasha, antardasha and pratyantardasha are computed and dated. |
| "It flatters and hooks you in" | The gate has no mechanism for producing an ungrounded claim, and the prompt forbids flattery. |
| "Reverify you are using sidereal only" | Sidereal Lahiri throughout; `meta.tradition` states no tropical calculation is mixed in. |

## Compatibility uses the same gate

`kosma/compatibility.py` does not get its own rule. It calls the same
`run_gate()`, with its own factor kinds — koota, dosha, overlay, cross-aspect,
Moon relationship, lagna relationship, dasha sync, varga — and the same
requirement that two distinct kinds agree before a topic can be stated. Topics
that fail are withheld exactly as houses are.

Three design decisions there are worth stating, because each was a choice
against the easier option:

**The score does not lead.** Ashtakoota is what people arrive expecting, and
putting "28/36" at the top would be the conventional move. But it weighs eight
Moon-derived factors and ignores both ascendants, the 7th house and its lord,
Venus, Mars, and the dashas in force — which is precisely the "you're 28/36, so
you're fine" trap practitioners criticise. The gated findings lead; the score
sits below them with its critique attached.

**Friendship mode drops kootas rather than reweighting them.** Yoni assesses
sexual compatibility and Nadi assesses genetic compatibility. Neither says
anything about a friendship. Computing them and asking the reader to discount
them would be worse than not computing them. Varna goes too, as directional and
marriage-shaped. What remains is honestly labelled as this project's
construction from classical parts, not as a classical scheme — the parts are
authoritative, the sum is a convenience.

**Three people are compared pairwise.** There is no classical method for
scoring a group as a whole. Averaging the pairs into a "group harmony score"
would be inventing a method, which is the one thing this codebase refuses to do
everywhere else.

Two data points carry social weight and are labelled wherever they appear — in
the module docstring, the koota's own `variant_note`, the UI, and here. **Varna**
is a classification by the Moon sign's element, not anyone's birth caste, and
says nothing about social standing. **Nadi** and **Bhakoot** doshas are used in
real social contexts to refuse matches, usually quoted without the classical
cancellation conditions; those conditions are computed and shown alongside. A
dosha is a flag to examine, not a disqualification of a person.

## The interface

The UI is deliberately instrument-shaped: near-black ground, hairline rules,
tabular numerals on every figure, one amber accent, and signal colour reserved
for actual signal. The argument it makes visually is that this thing measures
something.

One constraint shaped it more than any aesthetic decision. The app ships
`Content-Security-Policy: style-src 'self'` with no `'unsafe-inline'`, so there
are no inline style attributes and therefore no server-set widths. Proportion
bars are drawn with block characters in the markup instead — which happens to
be exactly the right look, and costs nothing. There is no build step, no
framework, and no external font or script; the CSP would block them anyway.

## Tradition separation

Vedic and Western are different computations, not a display toggle. This
codebase computes sidereal Lahiri only and says so in `meta`. There is no
tropical code path to accidentally cross into.

If Western is ever added it belongs in a separate module with its own chart
type and its own evidence rules, sharing only the UI. Building it as a flag on
the existing engine would guarantee an eventual bug where a tropical longitude
is read by a sidereal rule — and that bug would be invisible in the output.

The same discipline applies within Jyotisha. KP is cusp-based and uses Placidus;
the rest of the engine uses whole-sign. Both are computed and **both are
reported** (`house_whole_sign` and `house_placidus`) rather than reconciled
into a single number that would be wrong for one of the two systems.

## Privacy and memory

These pull in opposite directions and the tension is real. A system that
forgets your dasha between sessions cannot answer a timing question. A system
that remembers is holding your birth data.

The resolution is that **the user holds the memory, not the server.**

`kosma/memory.py` writes an encrypted file locally: scrypt-derived key, Fernet
authenticated encryption, owner-only permissions where the platform honours
them. The server has no endpoint that accepts it and never sees the passphrase.
Continuity comes from the user attaching their own file to a session.

A chart fingerprint — a one-way digest of the computed positions — lets a
memory file prove which chart it belongs to without containing the birth
details. Mismatched memory is attached with a warning rather than silently
trusted or silently dropped. Memory is also labelled as context, not
instruction, so notes in a file cannot function as directives to the model.

`cryptography` is an optional extra so the default install stays minimal and
the pinned runtime set stays easy to keep CVE-clean.

## What this does not solve

Being straight about the limits is part of the design.

- **Expert curation is a process, not a data structure.** Every rule here cites
  a text, which makes review *possible* — a practitioner can check any line
  against BPHS or Phaladeepika. It does not make review *done*. A maintained
  knowledge base needs practising astrologers reviewing it on an ongoing basis,
  and that is an operational commitment no repository layout can substitute
  for. See `CONTRIBUTING.md` for the checklist a rule change must pass.
- **Shadbala is incomplete and says so.** Varsha bala, masa bala and yuddha
  bala are not computed. Every result carries an `omitted` list and
  `complete: False`, and the totals should not be read against the classical
  minimum thresholds as though whole.
- **The gate tests structure, not truth.** It establishes that a claim has
  classical support in this chart. Whether Jyotisha itself predicts anything is
  a separate question the code takes no position on.
- **Some things are genuinely contested and stay contested.** D60 counting in
  even signs, purushartha assignment, nodal aspects, Kalapurusha body parts.
  These are flagged rather than resolved, because resolving them would mean
  picking a school and hiding that we had.
- **Birth time dominates everything.** The ascendant moves a degree every four
  minutes. A ten-minute error changes the lagna pada and several KP
  sub-divisions. No amount of downstream rigour repairs a bad input, which is
  why `birth.accuracy_note` travels inside the pack.
- **Regional weightings are not modelled.** Kerala practice weights
  ashtakavarga differently from North Indian Parashari, and both differ from
  Jaimini. This engine implements one defensible reading of each rule and cites
  it, so a practitioner can see what they would need to change.

## Using it

```bash
# readable structural summary
python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK" --format report

# the pack, for your own tooling
python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK" --format json

# prompt + pack, ready to paste into a Project or an API call
python -m kosma --date 2000-01-01 --time 12:00 --city "London, UK" --format bundle
```

For a Claude Project: put `prompts/system_prompt.md` in the project
instructions, and the pack from `--format json` in project knowledge. The model
then has no reason to calculate and no room to invent, because everything it
needs is already resolved and everything it may not say is already marked.

## Prior art

Two libraries informed the calculation surface. [jyotishganit] shaped the
coverage target — full D1–D60 vargas, shadbala, Bhinna and Sarva ashtakavarga,
and a single serialisable birth-chart object, which is what the grounding pack
became. [VedicAstro] shaped the KP layer: the ABCD significator table, cusp-based
Placidus houses kept distinct from the sign-based ones, and the separation of
calculation from presentation.

[jyotishganit]: https://github.com/northtara/jyotishganit
[VedicAstro]: https://github.com/diliprk/VedicAstro
