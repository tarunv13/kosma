"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import type { Gender } from "@/types/chart";
import CosmicCard from "@/components/CosmicCard";
import DashaTimeline from "@/components/DashaTimeline";
import EvidencePanel from "@/components/EvidencePanel";
import HousesPanel from "@/components/HousesPanel";
import NumerologyPanel from "@/components/NumerologyPanel";
import PlacementsPanel from "@/components/PlacementsPanel";
import VedicChartEngine from "@/components/VedicChartEngine";
import { useChartStore } from "@/store/useChartStore";

/**
 * The shell is a twelve-column grid at xl and above. Below that it collapses
 * to a single column — but on a wide display the chart and the findings sit
 * side by side and fill the space, rather than stacking into a narrow ribbon
 * down the middle.
 */

function BirthForm() {
  const load = useChartStore((s) => s.load);
  const loading = useChartStore((s) => s.loading);
  const error = useChartStore((s) => s.error);
  const chart = useChartStore((s) => s.chart);
  const [form, setForm] = useState({
    name: "",
    birth_date: "2000-01-01",
    birth_time: "12:00",
    city: "London, UK",
    gender: "unspecified" as Gender,
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void load(form);
      }}
      className="panel"
    >
      <div className="panel-head">
        <h2 className="heading text-xl">Cast a chart</h2>
        <span className="eyebrow">
          the ascendant moves a degree every four minutes
        </span>
      </div>

      <div className="panel-body">
        <div className="grid items-end gap-5 lg:grid-cols-[1.1fr_1fr_0.8fr_1.3fr_0.9fr_auto]">
          <label className="block">
            <span className="eyebrow mb-2 block">Name</span>
            <input
              className="field-input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="optional"
              maxLength={80}
            />
          </label>
          <label className="block">
            <span className="eyebrow mb-2 block">Date of birth</span>
            <input
              type="date"
              required
              className="field-input"
              value={form.birth_date}
              onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="eyebrow mb-2 block">Time</span>
            <input
              type="time"
              required
              step={60}
              className="field-input"
              value={form.birth_time}
              onChange={(e) => setForm({ ...form, birth_time: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="eyebrow mb-2 block">Birthplace</span>
            <input
              className="field-input"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              placeholder="City, Country"
            />
          </label>
          {/*
            Optional, and it says so. Several kootas are stated in the texts as
            a rule about the bride relative to the groom, so the roles change a
            compatibility score; the natal reading does not use it at all.
          */}
          <label className="block">
            <span className="eyebrow mb-2 block">Gender</span>
            <select
              className="field-input"
              value={form.gender}
              onChange={(e) =>
                setForm({ ...form, gender: e.target.value as Gender })
              }
            >
              <option value="unspecified">Prefer not to say</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
            </select>
          </label>
          <button type="submit" disabled={loading} className="btn-primary h-[3.25rem]">
            {loading ? "Computing…" : chart ? "Recompute" : "Compute"}
          </button>
        </div>

        <p className="mt-3 text-meta leading-relaxed text-ink-2">
          Gender is optional and changes nothing in a single chart. It is used
          only in comparison, where several kootas are stated in the classical
          texts as a rule about the bride relative to the groom — without it,
          the engine falls back to the order you entered and says so.
        </p>

        {error && (
          <p className="mt-4 rounded-lg border border-neg/40 bg-neg-wash px-4 py-3 text-meta font-medium text-neg">
            {error}
          </p>
        )}
      </div>
    </form>
  );
}

export default function Page() {
  const chart = useChartStore((s) => s.chart);

  return (
    <div className="space-y-6">
      {!chart && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid gap-10 pb-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:items-center"
        >
          <div>
            <h1 className="heading mb-5 text-4xl leading-[1.1]">
              A living chart that admits
              <br className="hidden sm:block" /> what it cannot see.
            </h1>
            <p className="max-w-[58ch] text-lg leading-relaxed text-ink-2">
              Positions come from the Swiss Ephemeris, Lahiri sidereal, resolved to
              the arc-second. Every reading is gated: an area of life appears only
              where two independent kinds of chart factor agree, and is listed as
              withheld where they do not.
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-2">
            {[
              ["Divisions", "D1 – D60"],
              ["Strength", "Shadbala + Ashtakavarga"],
              ["Timing", "Vimshottari + gochara"],
              ["Every claim", "cited to its text"],
            ].map(([k, v]) => (
              <div key={k} className="rounded-xl border border-slate-200/90 bg-vellum p-4 shadow-sm">
                <dt className="eyebrow mb-1">{k}</dt>
                <dd className="font-serif text-lg text-ink">{v}</dd>
              </div>
            ))}
          </dl>
        </motion.section>
      )}

      <BirthForm />

      <AnimatePresence>
        {chart && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="grid grid-cols-1 gap-6 xl:grid-cols-12"
          >
            <div className="xl:col-span-5">
              <VedicChartEngine />
            </div>
            <div className="xl:col-span-7">
              <EvidencePanel />
            </div>

            <div className="xl:col-span-12">
              <DashaTimeline />
            </div>

            <div className="xl:col-span-12">
              <PlacementsPanel />
            </div>

            <div className="xl:col-span-12">
              <HousesPanel />
            </div>

            <div className="xl:col-span-12">
              <NumerologyPanel />
            </div>

            <section className="xl:col-span-12">
              <div className="mb-5 flex flex-wrap items-baseline justify-between gap-3">
                <h2 className="heading text-2xl">
                  Yogas formed
                  <span className="ml-3 font-mono text-lg font-bold text-ink-3">
                    {chart.yogas.length}
                  </span>
                </h2>
                <span className="eyebrow">absent means not formed, not omitted</span>
              </div>
              {chart.yogas.length === 0 ? (
                <p className="panel panel-body text-base text-ink-2">
                  No yoga in the implemented rule set is formed in this chart.
                </p>
              ) : (
                <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
                  {chart.yogas.map((y) => (
                    <CosmicCard key={`${y.name}-${y.planets.join("-")}`} yoga={y} />
                  ))}
                </div>
              )}
            </section>

            <section className="panel xl:col-span-12">
              <div className="panel-head">
                <h2 className="heading text-xl">Reckoning</h2>
                <span className="eyebrow">{chart.chart_meta.computed_at}</span>
              </div>
              <div className="panel-body">
                <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2 lg:grid-cols-4">
                  {[
                    ["Ayanamsa", chart.chart_meta.ayanamsa],
                    ["Value", `${chart.chart_meta.ayanamsa_value.toFixed(4)}°`],
                    ["Zodiac", chart.chart_meta.zodiac],
                    ["Houses", chart.chart_meta.house_system],
                    ["Vara", chart.panchanga.vara],
                    ["Tithi", `${chart.panchanga.paksha} ${chart.panchanga.tithi}`],
                    ["Yoga", chart.panchanga.yoga],
                    ["Karana", chart.panchanga.karana],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <dt className="eyebrow mb-1.5">{k}</dt>
                      <dd className="tnum text-meta font-medium leading-relaxed text-ink">{v}</dd>
                    </div>
                  ))}
                </dl>
                <p className="mt-6 border-t border-slate-200/90 pt-5 text-meta leading-relaxed text-ink-2">
                  {chart.disclaimer}
                </p>
              </div>
            </section>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
