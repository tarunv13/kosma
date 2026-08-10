"use client";

import { useState } from "react";
import { useChartStore } from "@/store/useChartStore";
import type { Planet } from "@/types/chart";

/**
 * What each graha is doing in the house it landed in.
 *
 * This is the section a reader goes looking for and the old interface never
 * had: not "Saturn 27.61° Capricorn" but what Saturn in the tenth house
 * actually means, what it gives, what it costs, how it shows in the person,
 * and what the tradition offers to work on the difficult side.
 *
 * The strengths and weaknesses are modulated server-side by the dignity the
 * planet actually holds here, so an exalted Saturn and a debilitated one do
 * not read identically. What is *not* here is a prediction: this states
 * classical signification, and the gate remains the only thing that decides
 * what may be asserted about a life.
 */

/** The symbol, with the two-letter form as its accessible label. */
function Sigil({ planet }: { planet: Planet }) {
  return (
    <span
      className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-300 bg-wash font-serif text-xl leading-none text-ink"
      title={planet.name}
      aria-label={planet.name}
    >
      {planet.symbol}
    </span>
  );
}

function PlacementRow({ planet }: { planet: Planet }) {
  const [open, setOpen] = useState(false);
  const p = planet.placement;

  return (
    <div className="border-b border-hair py-5 last:border-0">
      <div className="flex flex-wrap items-center gap-3">
        <Sigil planet={planet} />
        <span className="text-base font-semibold text-ink">
          {planet.name}
          <span className="ml-2 font-mono text-micro font-medium text-ink-2">
            {planet.glyph}
          </span>
        </span>
        <span className="font-mono text-micro font-medium text-ink-2">
          house {p.house} · {p.sign} · {p.dignity}
        </span>
        {planet.retrograde && (
          <span className="chip chip-muted" title="retrograde">
            ℞
          </span>
        )}
        {p.classes.map((c) => (
          <span key={c} className="chip chip-muted">
            {c}
          </span>
        ))}
      </div>

      <p className="mt-3 text-base leading-relaxed text-ink">{p.signifies}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-pos/25 bg-pos-wash p-4">
          <span className="eyebrow mb-1.5 block text-pos">Strengths</span>
          <p className="text-meta leading-relaxed text-ink-2">{p.strengths}</p>
        </div>
        <div className="rounded-xl border border-neg/25 bg-neg-wash p-4">
          <span className="eyebrow mb-1.5 block text-neg">Weaknesses</span>
          <p className="text-meta leading-relaxed text-ink-2">{p.weaknesses}</p>
        </div>
      </div>

      <p className="mt-3 text-base leading-relaxed text-ink-2">{p.nature}</p>

      {/* The part that is about this chart rather than the abstract pairing. */}
      <p className="mt-3 border-l-2 border-gold/50 pl-3 text-meta leading-relaxed text-ink-2">
        {p.condition}
      </p>

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="mt-3 font-mono text-micro font-bold text-gold underline decoration-gold/40 underline-offset-4 transition-colors hover:decoration-gold"
      >
        {open ? "hide remedy and classical notes" : "remedy and classical notes"}
      </button>

      {open && (
        <div className="mt-3 space-y-3 rounded-xl bg-wash p-4">
          {p.notable && (
            <p className="text-meta leading-relaxed text-ink-2">{p.notable}</p>
          )}
          {p.class_note && (
            <p className="text-meta leading-relaxed text-ink-2">{p.class_note}</p>
          )}

          <div>
            <span className="eyebrow mb-1.5 block">
              Upaya for {p.remedy.graha}
            </span>
            <dl className="grid gap-x-6 gap-y-1.5 sm:grid-cols-2">
              {[
                ["Mantra", `${p.remedy.mantra} — ${p.remedy.transliteration}`],
                ["Day", p.remedy.vara],
                ["Daana", p.remedy.daana],
                ["Ratna", p.remedy.gem],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <dt className="font-mono text-micro font-bold text-ink-3">{k}</dt>
                  <dd className="text-meta text-ink-2">{v}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-2 text-meta leading-relaxed text-ink">
              {p.remedy.practical}
            </p>
          </div>

          <p className="text-micro leading-relaxed text-ink-3">
            {p.remedy.caveat} {p.remedy.ratna_caveat}
          </p>
        </div>
      )}
    </div>
  );
}

export default function PlacementsPanel() {
  const chart = useChartStore((s) => s.chart);
  if (!chart) return null;

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="heading text-xl">Each planet, and what it is doing</h2>
        <span className="eyebrow">signification, not prediction</span>
      </div>
      <div className="panel-body">
        <p className="mb-4 max-w-[70ch] text-meta leading-relaxed text-ink-2">
          What the classical texts hold each graha to mean in the bhava it
          occupies here, with the strengths and weaknesses weighted by the
          dignity it actually holds in this chart. This section states
          signification; whether anything may be <em>claimed</em> about a life
          is decided by the gate above, not here.
        </p>
        {chart.planets.map((planet) => (
          <PlacementRow key={planet.id} planet={planet} />
        ))}
      </div>
    </section>
  );
}
