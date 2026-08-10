"use client";

import { useState } from "react";
import HouseDossier from "@/components/HouseDossier";
import { useChartStore } from "@/store/useChartStore";

/**
 * All twelve houses, whether or not the gate had anything to say about them.
 *
 * The findings panel above reports only where two independent kinds of factor
 * agreed, which is the right rule for a *claim*. But it left a reader unable
 * to see the structure of their own chart: eight houses reported, four
 * withheld, and no way to learn what the fourth house even governs.
 *
 * Structure is not prediction, so it needs no gate. This says what each house
 * covers, what sign is on it, who rules it and where that ruler went. The
 * moment anything crosses from structure into assertion about a life, it
 * belongs upstairs behind the gate instead.
 */

export default function HousesPanel() {
  const chart = useChartStore((s) => s.chart);
  const [open, setOpen] = useState<number | null>(null);
  const setHoveredHouse = useChartStore((s) => s.setHoveredHouse);

  if (!chart) return null;

  const reported = new Set(chart.findings.map((f) => f.house));

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="heading text-xl">All twelve houses</h2>
        <span className="eyebrow">what each one governs</span>
      </div>
      <div className="panel-body">
        <p className="mb-4 max-w-[70ch] text-meta leading-relaxed text-ink-2">
          The structure of the whole chart, including the houses the gate
          declined to report on. Describing what a house governs and who rules
          it is not a claim about your life, so it needs no corroboration —
          which is exactly why it sits apart from the findings.
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          {chart.houses.map((h) => (
            <div
              key={h.house}
              onMouseEnter={() => setHoveredHouse(h.house)}
              onMouseLeave={() => setHoveredHouse(null)}
              className="rounded-xl border border-slate-200/90 bg-vellum p-4 shadow-sm"
            >
              <div className="mb-1.5 flex flex-wrap items-baseline gap-2">
                <span className="rounded-md border border-slate-300 bg-wash px-1.5 py-0.5 font-mono text-micro font-bold text-ink-2">
                  H{String(h.house).padStart(2, "0")}
                </span>
                <span className="text-base font-semibold text-ink">{h.topic}</span>
                <span className="ml-auto font-mono text-micro font-medium text-ink-2">
                  {h.sign}
                </span>
              </div>

              <p className="text-meta leading-relaxed text-ink-2">{h.governs}</p>

              <p className="mt-2 font-mono text-micro leading-relaxed text-ink-3">
                ruled by {h.lord}, which sits in house {h.lord_placement.in_house} (
                {h.lord_placement.in_sign}, {h.lord_placement.dignity})
                {" · "}
                {h.sarvashtakavarga} points, {h.sarvashtakavarga_band}
              </p>

              <div className="mt-2 flex flex-wrap items-center gap-2">
                {h.occupants.length > 0 ? (
                  h.occupants.map((o) => (
                    <span
                      key={o.name}
                      className="chip chip-muted"
                      title={`${o.name} — ${o.dignity}`}
                    >
                      {o.symbol} {o.glyph}
                      {o.retrograde ? " ℞" : ""}
                    </span>
                  ))
                ) : (
                  <span className="font-mono text-micro text-ink-3">
                    no planet sits here
                  </span>
                )}
                {!reported.has(h.house) && (
                  <span className="chip chip-muted" title="the gate withheld a reading">
                    not reported
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={() => setOpen(open === h.house ? null : h.house)}
                className="mt-3 font-mono text-micro font-medium text-ink-2 underline decoration-slate-400 underline-offset-4 transition-colors hover:text-gold"
              >
                {open === h.house ? "hide detail" : "full detail"}
              </button>

              {open === h.house && (
                <div className="mt-3">
                  <HouseDossier house={h} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
