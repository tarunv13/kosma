"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import HouseDossier from "@/components/HouseDossier";
import { useChartStore } from "@/store/useChartStore";
import type { Finding } from "@/types/chart";

/**
 * What the chart will and will not support.
 *
 * This panel is the reason the rest of the interface is allowed to be
 * beautiful. Withheld topics render at the same visual weight as findings
 * rather than as a footnote: the point of the gate is that "the chart does not
 * show this" is a result, not an absence.
 */

function verdictChip(verdict: string) {
  if (verdict === "supported")
    return <span className="chip chip-pos">supported</span>;
  if (verdict === "under strain")
    return <span className="chip chip-neg">under strain</span>;
  if (verdict.startsWith("contested"))
    return <span className="chip chip-nebula">contested</span>;
  return <span className="chip chip-muted">{verdict}</span>;
}

function FindingRow({ finding, onFocus }: { finding: Finding; onFocus: () => void }) {
  const [open, setOpen] = useState(false);
  const [dossier, setDossier] = useState(false);
  const evidence = useChartStore((s) => s.chart?.evidence ?? []);
  const house = useChartStore((s) =>
    s.chart?.houses.find((h) => h.house === finding.house),
  );
  const cited = evidence.filter((e) => finding.citations.includes(e.id));
  const labels = useChartStore((s) => s.chart?.kind_labels ?? {});
  const plain = finding.plain;

  return (
    <div
      className="border-b border-hair py-4 last:border-0"
      onMouseEnter={onFocus}
    >
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="rounded-md border border-slate-300 bg-wash px-1.5 py-0.5 font-mono text-micro font-bold text-ink-2">
          H{String(finding.house).padStart(2, "0")}
        </span>
        <span className="min-w-[12rem] flex-1 text-base font-semibold text-ink">
          {finding.topic}
        </span>
        {verdictChip(finding.verdict)}
      </div>

      {/*
        The reading, in ordinary English, before any of the machinery. This is
        what someone who has not read Parashara came for; the verdict word, the
        factor kinds and the ledger are all still here, one disclosure away.
      */}
      <div className="mt-3 pl-10">
        <p className="text-base font-medium leading-relaxed text-ink">
          {plain.headline}
        </p>
        {plain.body.map((line) => (
          <p key={line} className="mt-2 text-base leading-relaxed text-ink-2">
            {line}
          </p>
        ))}
        <p className="mt-3 border-l-2 border-slate-300 pl-3 text-meta leading-relaxed text-ink-2">
          {plain.limit}
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 pl-10">
        <button
          type="button"
          onClick={() => setDossier((v) => !v)}
          className="font-mono text-micro font-bold text-gold underline decoration-gold/40 underline-offset-4 transition-colors hover:decoration-gold"
        >
          {dossier ? "hide house" : "what's in this house"}
        </button>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="font-mono text-micro font-medium text-ink-2 underline decoration-slate-400 underline-offset-4 transition-colors hover:text-gold"
        >
          {open
            ? "hide the chart evidence"
            : `show the chart evidence (${finding.citations.length})`}
        </button>
      </div>

      {dossier && house && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="mt-3 overflow-hidden pl-10"
        >
          <HouseDossier house={house} />
        </motion.div>
      )}

      {open && (
        <motion.ul
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="mt-3 space-y-2 overflow-hidden rounded-xl bg-wash p-4 pl-6"
        >
          <li className="mb-1 border-b border-hair pb-3">
            <span className="font-mono text-micro font-bold uppercase tracking-wider text-ink-2">
              {finding.confidence}
            </span>
            <span className="mt-1 block text-meta leading-relaxed text-ink-2">
              {finding.verdict}
            </span>
            <span className="mt-2 flex flex-wrap gap-1.5">
              {/* The factor kinds, named in English rather than in schema keys. */}
              {finding.kinds.map((k) => (
                <span key={k} className="chip chip-muted" title={k}>
                  {labels[k] ?? k.replace(/_/g, " ")}
                </span>
              ))}
            </span>
          </li>
          {cited.map((e) => (
            <li key={e.id} className="text-meta leading-relaxed text-ink-2">
              <span className="font-mono text-micro font-bold text-ink-2">{e.id}</span>{" "}
              <span
                className={
                  e.polarity > 0
                    ? "font-mono font-bold text-pos"
                    : e.polarity < 0
                      ? "font-mono font-bold text-neg"
                      : "font-mono text-ink-3"
                }
              >
                {e.polarity > 0 ? "+" : e.polarity < 0 ? "−" : "="}
              </span>{" "}
              {e.statement}
              {e.disputed && (
                <span className="ml-1 text-gold" title="disputed between authorities">
                  ⚠
                </span>
              )}
              <span className="mt-1 block font-mono text-micro text-ink-3">
                {e.source}
              </span>
            </li>
          ))}
        </motion.ul>
      )}
    </div>
  );
}

/**
 * A withheld topic still gets its structure.
 *
 * The gate refuses a *verdict*, not the facts. Which sign is on the house and
 * where its lord went are computed either way, and hiding them would suggest
 * the engine knows less than it does.
 */
function WithheldDossier({ house }: { house: number }) {
  const [open, setOpen] = useState(false);
  const data = useChartStore((s) => s.chart?.houses.find((h) => h.house === house));
  if (!data) return null;
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="mt-3 font-mono text-micro font-bold text-ink-2 underline decoration-slate-400 underline-offset-4 transition-colors hover:text-gold"
      >
        {open ? "hide house" : "show what is here anyway"}
      </button>
      {open && (
        <div className="mt-3">
          <HouseDossier house={data} />
        </div>
      )}
    </>
  );
}

export default function EvidencePanel() {
  const chart = useChartStore((s) => s.chart);
  const setHoveredHouse = useChartStore((s) => s.setHoveredHouse);
  if (!chart) return null;

  return (
    <div className="space-y-6">
      <section className="panel">
        <div className="panel-head">
          <h2 className="heading text-xl">Findings</h2>
          <span className="eyebrow">
            {chart.gate.minimum_agreeing_kinds} agreeing factors required
          </span>
        </div>
        <div className="panel-body">
          <p className="mb-2 max-w-[64ch] text-meta leading-relaxed text-ink-2">
            Each area was tested against nine kinds of chart factor. It is reported
            only where at least two <em>different</em> kinds agree; a kind that
            cancels itself out casts no vote.
          </p>
          <div onMouseLeave={() => setHoveredHouse(null)}>
            {chart.findings.map((f) => (
              <FindingRow
                key={f.house}
                finding={f}
                onFocus={() => setHoveredHouse(f.house)}
              />
            ))}
          </div>
        </div>
      </section>

      {chart.withheld.length > 0 && (
        <section className="panel border-neg/25">
          <div className="panel-head border-neg/20 bg-neg-wash">
            <h2 className="heading text-xl text-neg">Withheld</h2>
            <span className="eyebrow text-neg">
              not supportable from this chart
            </span>
          </div>
          <div className="panel-body">
            <p className="mb-4 max-w-[64ch] text-meta leading-relaxed text-ink-2">
              These were tested and no direction reached the threshold. That is a
              result, not a gap — any reading of them would be invention.
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              {chart.withheld.map((w) => (
                <div
                  key={w.house}
                  onMouseEnter={() => setHoveredHouse(w.house)}
                  onMouseLeave={() => setHoveredHouse(null)}
                  className="rounded-xl border border-neg/20 bg-neg-wash p-4"
                >
                  <div className="mb-1.5 flex items-baseline gap-2">
                    <span className="font-mono text-micro font-bold text-neg">
                      H{String(w.house).padStart(2, "0")}
                    </span>
                    <span className="text-base font-semibold text-ink">{w.topic}</span>
                    <span className="ml-auto font-mono text-micro font-medium text-ink-2">
                      {chart.houses.find((h) => h.house === w.house)?.sign}
                    </span>
                  </div>
                  {/* Plain first here too: a refusal is the easiest thing in
                      this interface to mistake for a bug, so it gets said in
                      full sentences before the technical reason. */}
                  <p className="text-base font-medium leading-relaxed text-ink">
                    {w.plain.headline}
                  </p>
                  {w.plain.body.map((line) => (
                    <p
                      key={line}
                      className="mt-2 text-meta leading-relaxed text-ink-2"
                    >
                      {line}
                    </p>
                  ))}
                  <p className="mt-3 border-l-2 border-neg/30 pl-3 font-mono text-micro leading-relaxed text-ink-2">
                    {w.reason}
                  </p>
                  <WithheldDossier house={w.house} />
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
