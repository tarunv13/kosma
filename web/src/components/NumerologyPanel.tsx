"use client";

import { useChartStore } from "@/store/useChartStore";
import type { NumberReading } from "@/types/chart";

/**
 * Numerology, beside the chart and deliberately outside the gate.
 *
 * It is here because it was asked for and because it travels with Jyotish in
 * practice. It is kept visually and structurally separate because it casts no
 * vote on any finding: the gate's claim is that two independent kinds of
 * *chart* factor must agree, and a number derived from a spelling is not one.
 * Folding it in would quietly weaken the only guarantee this project makes.
 */

function NumberCard({ label, reading }: { label: string; reading: NumberReading }) {
  return (
    <div className="rounded-xl border border-slate-200/90 bg-vellum p-4 shadow-sm">
      <div className="mb-2 flex items-baseline gap-3">
        <span className="eyebrow">{label}</span>
        <span className="ml-auto font-serif text-3xl leading-none text-ink">
          {reading.number}
        </span>
      </div>
      <p className="font-mono text-micro font-bold text-gold">{reading.graha}</p>
      <p className="mt-1.5 text-meta leading-relaxed text-ink-2">{reading.meaning}</p>
      <p className="mt-2 text-micro leading-relaxed text-ink-3">{reading.method}</p>
    </div>
  );
}

export default function NumerologyPanel() {
  const chart = useChartStore((s) => s.chart);
  if (!chart) return null;
  const n = chart.numerology;

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="heading text-xl">Numerology</h2>
        <span className="eyebrow">beside the chart, not inside it</span>
      </div>
      <div className="panel-body">
        <p className="mb-4 max-w-[70ch] text-meta leading-relaxed text-ink-2">
          {n.note}
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          <NumberCard label="Mulank · root number" reading={n.mulank} />
          <NumberCard label="Bhagyank · destiny number" reading={n.bhagyank} />
          {n.name_chaldean && (
            <NumberCard label="Name · Chaldean" reading={n.name_chaldean} />
          )}
          {n.name_pythagorean && (
            <NumberCard label="Name · Pythagorean" reading={n.name_pythagorean} />
          )}
        </div>

        {n.disagreement && (
          <p className="mt-4 rounded-xl border border-gold/40 bg-gold-wash p-4 text-meta leading-relaxed text-ink-2">
            {n.disagreement}
          </p>
        )}

        {(n.name_chaldean || n.name_pythagorean) && (
          <p className="mt-3 text-micro leading-relaxed text-ink-3">{n.name_note}</p>
        )}

        {!n.name_chaldean && (
          <p className="mt-3 text-meta leading-relaxed text-ink-2">
            Name numbers need a name. The date-derived numbers above do not, and
            are the ones classical Indian practice leans on anyway.
          </p>
        )}
      </div>
    </section>
  );
}
