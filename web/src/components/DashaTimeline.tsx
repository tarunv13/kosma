"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useMemo, useRef, useState } from "react";
import { formatYear } from "@/lib/api";
import { useChartStore } from "@/store/useChartStore";
import type { DashaPeriod } from "@/types/chart";

/**
 * The Time River.
 *
 * A horizontal scroll of mahadashas, each sized in proportion to its actual
 * length — Venus really is twenty years wide next to Sun's six, and squashing
 * them to equal boxes would throw away the one thing the vimshottari cycle is
 * telling you. Opening a period reveals its antardashas at the same scale.
 */

/** Tinted from the top so the lord reads at a glance without shouting. */
const LORD_HUE: Record<string, string> = {
  Sun: "from-amber-200/70 to-white",
  Moon: "from-slate-200/70 to-white",
  Mars: "from-red-200/60 to-white",
  Mercury: "from-emerald-200/60 to-white",
  Jupiter: "from-yellow-200/70 to-white",
  Venus: "from-pink-200/60 to-white",
  Saturn: "from-indigo-200/60 to-white",
  Rahu: "from-violet-200/60 to-white",
  Ketu: "from-fuchsia-200/55 to-white",
};

const PX_PER_YEAR = 34;
const DAYS_PER_YEAR = 365.25;

function width(period: DashaPeriod): number {
  return Math.max(
    46,
    ((period.to_jd - period.from_jd) / DAYS_PER_YEAR) * PX_PER_YEAR,
  );
}

export default function DashaTimeline() {
  const chart = useChartStore((s) => s.chart);
  const focusedJd = useChartStore((s) => s.focusedJd);
  const setFocusedJd = useChartStore((s) => s.setFocusedJd);
  const [expanded, setExpanded] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion() ?? false;

  const timeline = chart?.dashas.timeline ?? [];
  const activeLord = chart?.dashas.current.mahadasha ?? null;

  const totalWidth = useMemo(
    () => timeline.reduce((sum, p) => sum + width(p) + 4, 0),
    [timeline],
  );

  if (!chart) return null;

  const open = (period: DashaPeriod) => {
    const key = `${period.lord}-${period.from_jd}`;
    setExpanded((prev) => (prev === key ? null : key));
    setFocusedJd(period.from_jd);
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="heading text-xl">Vimshottari</h2>
        <span className="eyebrow">
          {chart.dashas.current.mahadasha} / {chart.dashas.current.antardasha} /{" "}
          {chart.dashas.current.pratyantardasha}
        </span>
      </div>
      <div className="panel-body">
      <p className="mb-5 text-meta text-ink-2">
        Widths are proportional to real duration. Click a period to open its
        antardashas.
      </p>

      <div
        ref={scroller}
        className="overflow-x-auto pb-3"
        role="group"
        aria-label="Mahadasha timeline"
      >
        <div style={{ minWidth: totalWidth }} className="flex gap-1.5">
          {timeline.map((period) => {
            const key = `${period.lord}-${period.from_jd}`;
            const isOpen = expanded === key;
            const isActive = period.status === "active";
            const hue = LORD_HUE[period.lord] ?? "from-wash to-white";

            return (
              <div key={key} style={{ width: width(period) }} className="shrink-0">
                <motion.button
                  type="button"
                  onClick={() => open(period)}
                  aria-expanded={isOpen}
                  whileHover={reduced ? undefined : { y: -2 }}
                  className={`relative h-20 w-full overflow-hidden rounded-xl border bg-gradient-to-b text-left transition-all ${hue} ${
                    isActive
                      ? "border-gold shadow-glow"
                      : isOpen
                        ? "border-ink-4"
                        : "border-slate-300 hover:border-slate-400"
                  } ${period.status === "past" ? "opacity-55" : ""}`}
                >
                  <span className="absolute left-2 top-2 font-mono text-meta font-bold text-ink">
                    {period.lord.slice(0, 2)}
                  </span>
                  {isActive && (
                    <span className="absolute right-2 top-2 h-2 w-2 animate-breathe rounded-full bg-gold-bright" />
                  )}
                  <span className="absolute bottom-2 left-2 font-mono text-micro font-medium text-ink-2">
                    {formatYear(period.from_jd)}
                  </span>
                </motion.button>

                {isOpen && period.children && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    transition={{ duration: reduced ? 0 : 0.3 }}
                    className="mt-1.5 flex gap-0.5 overflow-hidden"
                  >
                    {period.children.map((child) => {
                      const share =
                        (child.to_jd - child.from_jd) /
                        (period.to_jd - period.from_jd);
                      return (
                        <button
                          key={`${child.lord}-${child.from_jd}`}
                          type="button"
                          onClick={() => setFocusedJd(child.from_jd)}
                          title={`${child.lord}: ${child.from} → ${child.to}`}
                          style={{ flexBasis: `${share * 100}%` }}
                          className={`h-9 min-w-0 shrink rounded-md border font-mono text-micro transition-colors ${
                            child.status === "active"
                              ? "border-gold bg-gold-wash font-bold text-gold"
                              : focusedJd === child.from_jd
                                ? "border-ink-4 bg-wash text-ink"
                                : "border-slate-300 bg-white text-ink-2 hover:bg-wash"
                          }`}
                        >
                          {child.lord.slice(0, 2)}
                        </button>
                      );
                    })}
                  </motion.div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {activeLord && (
        <p className="mt-5 text-meta text-ink-2">
          Running{" "}
          <span className="font-mono font-medium text-gold">
            {chart.dashas.current.mahadasha}
          </span>{" "}
          mahadasha. A period marks which themes are live; it does not schedule
          an event.
        </p>
      )}
      </div>
    </section>
  );
}
