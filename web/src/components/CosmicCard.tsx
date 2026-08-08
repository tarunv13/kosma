"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useId, useState } from "react";
import { REMEDIES, RATNA_CAVEAT, REMEDY_CAVEAT } from "@/lib/remedies";
import { useChartStore } from "@/store/useChartStore";
import type { Yoga } from "@/types/chart";

/**
 * A yoga rendered as an artifact rather than a bullet point.
 *
 * The visual language is generous; the claims underneath are not. A card
 * always shows the classical rule that formed it and the text it comes from,
 * a disputed yoga is dimmed and labelled rather than quietly dropped, and
 * nothing is framed as earned or unlocked — a chart is not an achievement.
 */

function Particles({ count = 14 }: { count?: number }) {
  const reduced = useReducedMotion() ?? false;
  if (reduced) return null;
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
      {Array.from({ length: count }, (_, i) => {
        const angle = (i / count) * Math.PI * 2;
        return (
          <motion.span
            key={i}
            className="absolute left-1/2 top-1/2 h-1.5 w-1.5 rounded-full bg-gold-bright"
            initial={{ opacity: 0.9, x: 0, y: 0, scale: 1 }}
            animate={{
              opacity: 0,
              x: Math.cos(angle) * (70 + (i % 4) * 22),
              y: Math.sin(angle) * (70 + (i % 3) * 18),
              scale: 0,
            }}
            transition={{ duration: 0.85, ease: "easeOut" }}
          />
        );
      })}
    </div>
  );
}

export default function CosmicCard({ yoga }: { yoga: Yoga }) {
  const [open, setOpen] = useState(false);
  const [burst, setBurst] = useState(0);
  const sootheHouses = useChartStore((s) => s.sootheHouses);
  const reduced = useReducedMotion() ?? false;
  const panelId = useId();

  const beneficial = yoga.polarity > 0 && !yoga.disputed;
  const challenging = yoga.polarity < 0;

  const accent = yoga.disputed
    ? "border-hair bg-wash"
    : beneficial
      ? "border-gold/30 bg-gold-wash shadow-glow"
      : challenging
        ? "border-sky-700/20 bg-sky-50"
        : "border-nebula/25 bg-nebula-wash";

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) {
      setBurst((n) => n + 1);
      sootheHouses(yoga.houses);
    } else {
      sootheHouses([]);
    }
  };

  const remedies = yoga.planets
    .map((p) => REMEDIES[p])
    .filter((r): r is NonNullable<typeof r> => Boolean(r));

  return (
    <motion.article
      layout
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 160, damping: 22 }}
      className={`panel panel-hover relative overflow-hidden border p-6 ${accent}`}
    >
      {burst > 0 && open && <Particles key={burst} />}

      <div className="mb-2 flex items-start justify-between gap-3">
        <h3 className="heading text-lg leading-snug">{yoga.name}</h3>
        {yoga.disputed ? (
          <span className="chip chip-muted shrink-0">no classical source</span>
        ) : beneficial ? (
          <span className="chip chip-gold shrink-0">auspicious</span>
        ) : challenging ? (
          <span className="chip shrink-0 border-sky-700/40 bg-sky-50 text-sky-900">
            challenging
          </span>
        ) : (
          <span className="chip chip-nebula shrink-0">mixed</span>
        )}
      </div>

      <p className="text-base leading-relaxed text-ink-2">{yoga.detail}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {yoga.planets.map((p) => (
          <span key={p} className="chip chip-muted">
            {p}
          </span>
        ))}
        {yoga.houses.map((h) => (
          <span key={h} className="chip chip-muted tnum">
            H{h}
          </span>
        ))}
      </div>

      <div className="rule my-4" />

      <p className="text-meta leading-relaxed text-ink-2">
        <span className="font-semibold text-ink">Rule.</span> {yoga.rule}
      </p>
      <p className="mt-2 font-mono text-micro leading-relaxed text-ink-3">
        {yoga.source}
      </p>
      {yoga.caveat && (
        <p className="mt-3 border-l-2 border-nebula/40 pl-3 text-meta italic leading-relaxed text-nebula">
          {yoga.caveat}
        </p>
      )}

      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        aria-controls={panelId}
        className="mt-5 w-full rounded-xl border border-slate-300 bg-white py-3 font-mono text-micro font-bold uppercase tracking-[0.12em] text-ink-2 shadow-sm transition-all hover:border-gold hover:bg-gold-wash hover:text-gold active:translate-y-px"
      >
        {open ? "Close upaya" : "Upaya"}
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={panelId}
            key="remedy"
            layout
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: reduced ? 0 : 0.35, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-3">
              <p className="text-meta leading-relaxed text-ink-2">{REMEDY_CAVEAT}</p>

              {remedies.map((r) => (
                <div
                  key={r.graha}
                  className="rounded-xl border border-hair bg-white p-4"
                >
                  <div className="mb-1.5 flex items-baseline justify-between">
                    <span className="font-serif text-lg text-gold">{r.graha}</span>
                    <span className="font-mono text-micro font-medium text-ink-2">
                      {r.vara}
                    </span>
                  </div>
                  <p className="text-xl leading-relaxed text-ink">{r.mantra}</p>
                  <p className="font-mono text-meta text-ink-3">{r.transliteration}</p>
                  <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-meta">
                    <dt className="text-ink-3">Daana</dt>
                    <dd className="text-ink-2">{r.daana}</dd>
                    <dt className="text-ink-3">Ratna</dt>
                    <dd className="text-ink-2">{r.gem}</dd>
                  </dl>
                </div>
              ))}

              <p className="text-meta leading-relaxed text-ink-3">{RATNA_CAVEAT}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}
