"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { fetchCompatibility } from "@/lib/api";
import type {
  CompatibilityResponse,
  Dosha,
  PairReport,
  PersonInput,
} from "@/types/chart";

/**
 * Compatibility across two or three charts.
 *
 * Findings lead; the koota score sits beneath them with its critique attached.
 * That ordering is the point: ashtakoota weighs eight Moon-derived factors and
 * ignores both ascendants, the 7th lord, Venus, Mars and the dashas in force,
 * so leading with "28/36" would foreground the weakest part of the method.
 */

const BLANK: PersonInput = { name: "", birth_date: "", birth_time: "", city: "" };

// Synthetic epochs, not people — the same ones the test suite pins against.
const SEED: PersonInput[] = [
  { name: "Epoch A", birth_date: "2000-01-01", birth_time: "12:00", city: "London, UK" },
  { name: "Epoch B", birth_date: "2010-06-21", birth_time: "06:00", city: "Indore, India" },
];

function verdictChip(verdict: string) {
  if (verdict === "supported") return <span className="chip chip-pos">supported</span>;
  if (verdict === "under strain") return <span className="chip chip-neg">under strain</span>;
  if (verdict.startsWith("contested")) return <span className="chip chip-nebula">contested</span>;
  return <span className="chip chip-muted">{verdict}</span>;
}

function doshaChip(d: Dosha) {
  if (!d.present) return <span className="chip chip-pos">absent</span>;
  if (d.cancelled) return <span className="chip chip-nebula">cancelled</span>;
  return <span className="chip chip-neg">present</span>;
}

function PersonFields({
  index,
  value,
  onChange,
  onRemove,
}: {
  index: number;
  value: PersonInput;
  onChange: (v: PersonInput) => void;
  onRemove?: () => void;
}) {
  const set = (k: keyof PersonInput, v: string) => onChange({ ...value, [k]: v });
  return (
    <div className="panel">
      <div className="panel-head">
        <h3 className="heading text-lg">
          {["First", "Second", "Third"][index]} person
        </h3>
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="font-mono text-micro font-bold text-neg underline decoration-neg/40 underline-offset-4"
          >
            remove
          </button>
        )}
      </div>
      <div className="panel-body space-y-4">
        <label className="block">
          <span className="eyebrow mb-2 block">Name</span>
          <input
            className="field-input"
            value={value.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="optional"
            maxLength={60}
          />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="eyebrow mb-2 block">Date of birth</span>
            <input
              type="date"
              required
              className="field-input"
              value={value.birth_date}
              onChange={(e) => set("birth_date", e.target.value)}
            />
          </label>
          <label className="block">
            <span className="eyebrow mb-2 block">Time</span>
            <input
              type="time"
              required
              step={60}
              className="field-input"
              value={value.birth_time}
              onChange={(e) => set("birth_time", e.target.value)}
            />
          </label>
        </div>
        <label className="block">
          <span className="eyebrow mb-2 block">Birthplace</span>
          <input
            className="field-input"
            value={value.city}
            onChange={(e) => set("city", e.target.value)}
            placeholder="City, Country"
          />
        </label>
      </div>
    </div>
  );
}

function Pair({ pair }: { pair: PairReport }) {
  const [tab, setTab] = useState<"findings" | "kootas" | "synastry" | "evidence">(
    "findings",
  );

  const tabs = [
    ["findings", `Findings · ${pair.findings.length}`],
    ["kootas", `${pair.milan.scheme.split(" ")[0]} · ${pair.milan.total}/${pair.milan.maximum}`],
    ["synastry", "Synastry"],
    ["evidence", `Evidence · ${pair.evidence.length}`],
  ] as const;

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="heading text-xl">
          {pair.a} <span className="text-ink-3">&amp;</span> {pair.b}
        </h2>
        <span className="eyebrow">
          {pair.findings.length} reported &middot; {pair.withheld.length} withheld
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 border-b border-slate-200/90 px-6 py-3">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            aria-pressed={tab === key}
            className={`rounded-lg border px-3 py-1.5 font-mono text-micro font-bold transition-all ${
              tab === key
                ? "border-gold bg-gold-wash text-gold shadow-sm"
                : "border-slate-300 bg-white text-ink-2 hover:bg-wash"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="panel-body">
        {tab === "findings" && (
          <div className="space-y-1">
            {pair.findings.map((f) => (
              <div key={f.topic} className="border-b border-slate-200/70 py-3 last:border-0">
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                  <span className="min-w-[11rem] flex-1 text-base font-semibold text-ink">
                    {f.topic}
                  </span>
                  {verdictChip(f.verdict)}
                  <span className="font-mono text-micro font-medium text-ink-2">
                    {f.confidence}
                  </span>
                </div>
                <p className="mt-1 text-meta text-ink-2">{f.description}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {f.kinds.map((k) => (
                    <span key={k} className="chip chip-muted">
                      {k.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>
            ))}

            {pair.withheld.length > 0 && (
              <div className="mt-5 rounded-xl border border-neg/25 bg-neg-wash p-4">
                <p className="mb-3 font-mono text-micro font-bold uppercase tracking-[0.14em] text-neg">
                  Withheld
                </p>
                {pair.withheld.map((w) => (
                  <div key={w.topic} className="mb-3 last:mb-0">
                    <p className="text-base font-semibold text-ink">{w.topic}</p>
                    <p className="text-meta leading-relaxed text-ink-2">{w.reason}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === "kootas" && (
          <div>
            <div className="mb-5 flex items-baseline gap-4">
              <span className="font-mono text-3xl font-bold text-ink">
                {pair.milan.total}
              </span>
              <span className="font-mono text-lg text-ink-3">
                / {pair.milan.maximum}
              </span>
              <span className="ml-auto font-mono text-meta text-ink-2">
                {pair.milan.percentage}%
              </span>
            </div>

            <div className="space-y-2">
              {pair.milan.kootas.map((k) => (
                <div
                  key={k.name}
                  className="grid grid-cols-[7rem_5rem_1fr] items-start gap-4 border-b border-slate-200/70 py-2.5 last:border-0"
                >
                  <span className="text-base font-semibold text-ink">
                    {k.name}
                    {k.variant_note && (
                      <span className="ml-1 text-gold" title={k.variant_note}>
                        ⚠
                      </span>
                    )}
                  </span>
                  <span
                    className={`font-mono text-meta font-bold ${
                      k.void ? "text-neg" : k.full ? "text-pos" : "text-ink-2"
                    }`}
                  >
                    {k.score} / {k.maximum}
                  </span>
                  <span className="text-meta leading-relaxed text-ink-2">
                    {k.detail}
                    {k.variant_note && (
                      <span className="mt-1 block text-ink-3">{k.variant_note}</span>
                    )}
                  </span>
                </div>
              ))}
            </div>

            <p className="mt-5 rounded-xl border border-gold/30 bg-gold-wash p-4 text-meta leading-relaxed text-ink">
              {pair.milan.critique}
            </p>

            <h4 className="heading mb-3 mt-6 text-lg">Dosha checks</h4>
            <div className="space-y-2">
              {pair.doshas.map((d) => (
                <div
                  key={d.name}
                  className="grid grid-cols-[11rem_6rem_1fr] items-start gap-4 border-b border-slate-200/70 py-2.5 last:border-0"
                >
                  <span className="text-base font-semibold text-ink">{d.name}</span>
                  {doshaChip(d)}
                  <span className="text-meta leading-relaxed text-ink-2">
                    {d.detail}
                    {d.cancellations.length > 0 && (
                      <span className="mt-1 block text-pos">
                        Cancelled: {d.cancellations.join("; ")}.
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-meta italic leading-relaxed text-ink-2">
              {pair.doshas[0]?.note}
            </p>
          </div>
        )}

        {tab === "synastry" && (
          <div className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              {(
                [
                  [`${pair.a}'s grahas in ${pair.b}'s houses`, pair.overlays.a_into_b],
                  [`${pair.b}'s grahas in ${pair.a}'s houses`, pair.overlays.b_into_a],
                ] as const
              ).map(([title, list]) => (
                <div key={title}>
                  <p className="eyebrow mb-3">{title}</p>
                  <div className="space-y-1">
                    {list.map((o) => (
                      <div
                        key={o.planet}
                        className="grid grid-cols-[4rem_3rem_1fr] items-baseline gap-3 border-b border-slate-200/70 py-1.5 last:border-0"
                      >
                        <span className="font-mono text-meta font-semibold text-ink">
                          {o.planet}
                        </span>
                        <span
                          className={`font-mono text-meta font-bold ${
                            o.polarity > 0
                              ? "text-pos"
                              : o.polarity < 0
                                ? "text-neg"
                                : "text-ink-3"
                          }`}
                        >
                          H{o.house}
                        </span>
                        <span className="text-meta text-ink-2">{o.theme}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {pair.cross_aspects.length > 0 && (
              <div>
                <p className="eyebrow mb-3">Cross-chart drishti</p>
                <div className="space-y-1">
                  {pair.cross_aspects.map((c, i) => (
                    <div key={i} className="border-b border-slate-200/70 py-1.5 last:border-0">
                      <span className="text-meta text-ink">
                        <span className="font-mono font-semibold">
                          {c.from_person}&rsquo;s {c.planet}
                        </span>{" "}
                        aspects{" "}
                        <span className="font-mono font-semibold">
                          {c.to_person}&rsquo;s {c.target}
                        </span>
                      </span>
                      <span className="block text-meta text-ink-3">{c.rule}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-xl border border-slate-200/90 bg-wash p-4">
              <p className="eyebrow mb-2">Dashas in force</p>
              <p className="text-meta leading-relaxed text-ink-2">
                {pair.dasha_sync.detail}
              </p>
              <p className="mt-2 text-meta leading-relaxed text-ink-3">
                {pair.navamsa_note}
              </p>
            </div>
          </div>
        )}

        {tab === "evidence" && (
          <ul className="space-y-2">
            {pair.evidence.map((e) => (
              <li
                key={e.id}
                className="border-b border-slate-200/70 py-2 text-meta leading-relaxed text-ink-2 last:border-0"
              >
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
                {e.disputed && <span className="ml-1 text-gold">⚠</span>}
                <span className="mt-0.5 block text-ink-3">{e.basis}</span>
                <span className="block font-mono text-micro text-ink-3">{e.source}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

export default function ComparePage() {
  const [people, setPeople] = useState<PersonInput[]>(SEED);
  const [mode, setMode] = useState<"relationship" | "friendship">("relationship");
  const [result, setResult] = useState<CompatibilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setResult(await fetchCompatibility(people, mode));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not compare these charts.");
    } finally {
      setLoading(false);
    }
  };

  const update = (i: number, v: PersonInput) =>
    setPeople((prev) => prev.map((p, idx) => (idx === i ? v : p)));

  return (
    <div className="space-y-6">
      {!result && (
        <div className="max-w-[62ch] pb-2">
          <h1 className="heading mb-4 text-3xl leading-tight">
            Two or three charts, weighed against each other.
          </h1>
          <p className="text-lg leading-relaxed text-ink-2">
            Findings lead. The koota score is reported beneath them with its
            critique, because eight Moon-derived factors are one input to a
            judgement and not the judgement.
          </p>
        </div>
      )}

      <form onSubmit={submit} className="space-y-6">
        <section className="panel">
          <div className="panel-head">
            <h2 className="heading text-xl">Reading</h2>
            <span className="eyebrow">
              three people are compared pairwise, never averaged
            </span>
          </div>
          <div className="panel-body">
            <div className="flex flex-wrap items-end gap-6">
              <label className="block">
                <span className="eyebrow mb-2 block">What are you comparing?</span>
                <div className="flex gap-1.5">
                  {(["relationship", "friendship"] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMode(m)}
                      aria-pressed={mode === m}
                      className={`rounded-lg border px-4 py-2.5 font-mono text-micro font-bold capitalize transition-all ${
                        mode === m
                          ? "border-gold bg-gold-wash text-gold shadow-sm"
                          : "border-slate-300 bg-white text-ink-2 hover:bg-wash"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </label>

              {people.length < 3 ? (
                <button
                  type="button"
                  onClick={() => setPeople((p) => [...p, { ...BLANK }])}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 font-mono text-micro font-bold text-ink-2 transition-all hover:border-slate-400 hover:bg-wash"
                >
                  + Add a third person
                </button>
              ) : null}

              <button type="submit" disabled={loading} className="btn-primary ml-auto">
                {loading ? "Comparing…" : "Compare"}
              </button>
            </div>

            <p className="mt-4 text-meta leading-relaxed text-ink-2">
              Friendship mode drops Yoni and Nadi — they assess sexual and genetic
              compatibility and say nothing about a friendship — and Varna, whose
              rule is directional and marriage-shaped.
            </p>

            {error && (
              <p className="mt-4 rounded-lg border border-neg/40 bg-neg-wash px-4 py-3 text-meta font-medium text-neg">
                {error}
              </p>
            )}
          </div>
        </section>

        <div
          className={`grid gap-6 ${people.length === 3 ? "xl:grid-cols-3" : "lg:grid-cols-2"}`}
        >
          {people.map((p, i) => (
            <PersonFields
              key={i}
              index={i}
              value={p}
              onChange={(v) => update(i, v)}
              onRemove={
                i === 2 ? () => setPeople((prev) => prev.slice(0, 2)) : undefined
              }
            />
          ))}
        </div>
      </form>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div
              className={`grid gap-5 ${
                result.people.length === 3 ? "lg:grid-cols-3" : "sm:grid-cols-2"
              }`}
            >
              {result.people.map((p) => (
                <div key={p.label} className="panel p-5">
                  <h3 className="heading mb-3 text-lg">{p.label}</h3>
                  <dl className="grid grid-cols-[5rem_1fr] gap-x-4 gap-y-1 text-meta">
                    <dt className="eyebrow pt-0.5">Born</dt>
                    <dd className="tnum text-ink">{p.datetime.replace("T", " · ")}</dd>
                    <dt className="eyebrow pt-0.5">Place</dt>
                    <dd className="text-ink">{p.place}</dd>
                    <dt className="eyebrow pt-0.5">Lagna</dt>
                    <dd className="tnum text-ink">
                      {p.ascendant} {p.ascendant_dms}
                    </dd>
                    <dt className="eyebrow pt-0.5">Moon</dt>
                    <dd className="text-ink">
                      {p.moon_sign} · {p.moon_nakshatra} {p.moon_pada}
                    </dd>
                  </dl>
                </div>
              ))}
            </div>

            {result.pairs.map((pair) => (
              <Pair key={`${pair.a}-${pair.b}`} pair={pair} />
            ))}

            <p className="panel panel-body text-meta leading-relaxed text-ink-2">
              {result.disclaimer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
