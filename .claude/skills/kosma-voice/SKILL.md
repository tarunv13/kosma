---
name: kosma-voice
description: >
  Write or revise any reader-facing text in KOSMA: house readings, planet
  placements, dasha descriptions, glossary entries, UI copy, PDF prose. Use
  whenever generated text or interface copy is added or changed, so a reading
  arrives as one connected passage in plain English rather than a stack of
  labelled fragments.
---

# The KOSMA reading voice

Every sentence a reader sees comes from `kosma/plainspeak.py`,
`kosma/placements.py`, `kosma/interpretations.py`, `kosma/numerology.py`, the
React components under `web/src/components/`, or the PDF sections in
`kosma/pdf_generator.py`. This describes how that text has to read.

Run the `humanizer` skill over any prose you write here before you commit it.
Everything below sits on top of it, and the em dash ban in particular is
absolute: the reading text contains no `—` and no `–`.

## The failure this exists to prevent

A house reading once arrived as four disconnected pieces:

```
H01  self, body, and life direction  contested
The 1st house pulls in two directions at once...
In its favour: a benefic planet has this house in view and the house is
generously supplied with points.
Against it: the planet that rules this part sits somewhere difficult...
These rules come from Brihat Parashara Hora Shastra, Krishnamurti Paddhati...
Two kinds of factor agree here, which is the minimum...
```

Each fragment is true. Together they are a filing system, not a reading. The
reader has to assemble the meaning themselves, and the citation line arrives
in the middle of the passage where it competes with the thing it supports.

## Order the information the way a reader meets it

A person reading their own chart wants four things, in this order. Write in
this order even when the data arrives in another.

1. **What this area of life is.** Ground them before saying anything about
   it. One sentence, ordinary words, no Sanskrit yet.
2. **What their chart says about it.** The answer they came for. One
   connected passage that carries both the supporting and the opposing
   material inside the same prose. Never a bulleted "for" list against an
   "against" list.
3. **How it tends to show up.** The lived, recognisable version. This is what
   makes someone read the next section instead of closing the tab, and it is
   the part that must never overreach: describe the pattern, not their life.
4. **What to do with it.** Something they can actually act on.

Then, and only then:

5. **How far to trust it.** The confidence, and what was excluded.
6. **Where it comes from.** Texts, chapters, the evidence ledger.

Citations go last. A reader tracking a sentence about their marriage should
not have to step over "Brihat Parashara Hora Shastra ch. 41" to reach the end
of the thought. The sources still appear in full; they appear after the
reading rather than inside it.

## Weave, do not list

Two facts about the same house belong in one sentence when a person would say
them in one sentence.

Fragmented:

> In its favour: a benefic planet has this house in view and the house is
> generously supplied with points. Against it: the planet that rules this part
> of the chart sits somewhere difficult.

Woven:

> The house itself is well stocked and has Jupiter's attention, but the planet
> that runs it went somewhere difficult, so the support tends to arrive
> without being asked for while anything you set out to build here takes
> longer than it should.

The second version says the same things and adds nothing. It reads as one
thought because the connective tissue between the facts is written down
instead of left for the reader to infer.

## Carry the thread between sections

Sections of a reading should know about each other. A house that came out
contested and a dasha that is currently running its lord are the same story
told twice, and the text should say so once. Where the data supports a link,
make it: "this is the house the period you are in now belongs to." Where it
does not, leave it alone. An invented link is worse than a missing one.

## Register

Plain, adult, unhurried. Closer to a good doctor explaining a scan than to a
horoscope column.

Keep the Sanskrit and gloss it in place on first use. `swakshetra (in its own
sign)` teaches; deleting it patronises and using it bare excludes. The second
use can stand alone.

Say "tends to", "often", "the tradition reads this as". Never "you are", "you
will", "this means you". The engine reports what a chart contains and what the
texts say about that. It does not tell a person who they are.

Do not console and do not warn. A hard placement gets described accurately and
then gets something useful attached to it.

## What the honesty rules already require

These are load-bearing and no rewrite may soften them:

- A withheld house gets full sentences explaining that the silence is the
  result. It is the single easiest thing in the interface to mistake for a
  bug.
- Disputed evidence is excluded from the narration exactly as it is excluded
  from the vote, and is disclosed rather than hidden.
- Remedies attach to a graha, never to a placement or a yoga. There is no
  canonical remedy for "Mars in the 7th".
- Numerology sits outside the gate and says so.
- Nothing in the plain layer may assert something the ledger does not support.
  The prose is a restatement, never an addition.

## Colour carries meaning

Each house has a theme colour set in `kosma/themes.py`, chosen from the
element and the graha the tradition already assigns it, not from whether the
reading came out well. Fire houses run warm, water houses run cool, and the
2nd house is green because it is the house of earth and holdings.

Never colour by verdict. Painting a difficult house red and an easy one green
tells the reader how to feel before they have read anything, and it makes the
8th house look like an error message.

## Checklist before committing reader-facing text

- Reads aloud as connected prose, not as labelled fields.
- Nothing a person would need to reread to connect.
- No em dashes, no en dashes.
- Citations after the reading, never inside it.
- Sanskrit glossed on first use.
- No sentence tells the reader who they are.
- The withheld case still refuses clearly.
- Colour comes from theme, not from verdict.
