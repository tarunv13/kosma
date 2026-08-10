"use client";

import { curveBasis, line } from "d3-shape";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useMemo } from "react";
import { CHART, CHART_TYPE } from "@/lib/theme";
import {
  houseForSign,
  selectPlanetsByHouse,
  signForHouse,
  useChartStore,
} from "@/store/useChartStore";
import {
  SIGN_ABBR,
  SOUTH_INDIAN_CELLS,
  type Planet,
  type VargaPosition,
} from "@/types/chart";

/**
 * The South Indian chart, drawn as a live field rather than a static map.
 *
 * Signs hold fixed positions in the 4×4 grid — that is what makes it South
 * Indian — so the ascendant is marked rather than rotated to the top left.
 *
 * The same grid draws any of the sixteen divisions. Drishti is only offered in
 * D1: aspects are computed in the rasi, and painting rasi aspects over a D9
 * grid would be asserting something the engine never calculated.
 */

const SIZE = 560;
const CELL = SIZE / 4;
const CENTER = SIZE / 2;

const cellFor = (signIndex: number) =>
  SOUTH_INDIAN_CELLS[signIndex] ?? { col: 0, row: 0 };

const cellCenter = (signIndex: number): [number, number] => {
  const { col, row } = cellFor(signIndex);
  return [col * CELL + CELL / 2, row * CELL + CELL / 2];
};

const ray = line<[number, number]>()
  .x((d) => d[0])
  .y((d) => d[1])
  .curve(curveBasis);

/** A drishti path bowed toward the middle, so rays never overlap the grid. */
function drishtiPath(from: [number, number], to: [number, number]): string {
  const mid: [number, number] = [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2];
  const pull = 0.42;
  const control: [number, number] = [
    mid[0] + (CENTER - mid[0]) * pull,
    mid[1] + (CENTER - mid[1]) * pull,
  ];
  return ray([from, control, to]) ?? "";
}

function PlanetGlyph({
  planet,
  index,
  faded,
  reduced,
  active,
  onSelect,
}: {
  planet: Planet;
  index: number;
  faded: boolean;
  reduced: boolean;
  active: boolean;
  onSelect: (id: string) => void;
}) {
  const tone = planet.retrograde
    ? CHART.neg
    : active
      ? CHART.gold
      : planet.benefic
        ? CHART.ink
        : CHART.ink2;

  return (
    <motion.g
      initial={reduced ? false : { opacity: 0, y: -8 }}
      animate={{ opacity: faded ? 0.3 : 1, y: 0 }}
      transition={{
        delay: reduced ? 0 : 0.2 + index * 0.05,
        type: "spring",
        stiffness: 190,
        damping: 20,
      }}
      className="cursor-pointer"
      onClick={() => onSelect(planet.id)}
      role="button"
      tabIndex={0}
      aria-label={`${planet.name} in ${planet.sign} at ${planet.degree_dms}${
        planet.retrograde ? ", retrograde" : ""
      }`}
    >
      {active && (
        <rect
          x={-8}
          y={-15}
          width={122}
          height={22}
          rx={4}
          fill={CHART.goldWash}
          stroke={CHART.goldBright}
          strokeWidth={0.8}
        />
      )}
      <text
        x={0}
        y={0}
        fill={tone}
        fontSize={CHART_TYPE.glyph}
        fontWeight={active || planet.retrograde ? 700 : 600}
        style={{ fontFamily: "var(--font-mono), monospace" }}
      >
        {planet.glyph}
        {planet.retrograde ? "℞" : ""}
      </text>
      <text
        x={planet.retrograde ? 46 : 36}
        y={0}
        fill={CHART.ink2}
        fontSize={CHART_TYPE.degree}
        fontWeight={500}
        style={{ fontFamily: "var(--font-mono), monospace" }}
      >
        {planet.degree.toFixed(2)}°
      </text>
      {planet.sandhi && (
        <circle cx={-12} cy={-5} r={3} fill={CHART.nebulaBright}>
          <title>Sandhi: within one degree of a sign boundary</title>
        </circle>
      )}
    </motion.g>
  );
}

/** Divisional charts carry no degrees, so the cell shows placement only. */
function VargaGlyph({
  position,
  index,
  reduced,
}: {
  position: VargaPosition;
  index: number;
  reduced: boolean;
}) {
  return (
    <motion.g
      initial={reduced ? false : { opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: reduced ? 0 : 0.15 + index * 0.04 }}
    >
      <text
        x={0}
        y={0}
        fill={position.vargottama ? CHART.gold : CHART.ink}
        fontSize={CHART_TYPE.glyph}
        fontWeight={position.vargottama ? 700 : 600}
        style={{ fontFamily: "var(--font-mono), monospace" }}
      >
        {position.glyph}
      </text>
      {position.vargottama && (
        <>
          <circle cx={36} cy={-5} r={3.5} fill={CHART.goldBright}>
            <title>Vargottama: same sign as in D1</title>
          </circle>
          <text
            x={46}
            y={0}
            fill={CHART.gold}
            fontSize={CHART_TYPE.sav}
            fontWeight={600}
            style={{ fontFamily: "var(--font-mono), monospace" }}
          >
            vgt
          </text>
        </>
      )}
    </motion.g>
  );
}

export default function VedicChartEngine() {
  const chart = useChartStore((s) => s.chart);
  const activePlanet = useChartStore((s) => s.activePlanet);
  const hoveredHouse = useChartStore((s) => s.hoveredHouse);
  const soothed = useChartStore((s) => s.soothedHouses);
  const activeVarga = useChartStore((s) => s.activeVarga);
  const setActivePlanet = useChartStore((s) => s.setActivePlanet);
  const setHoveredHouse = useChartStore((s) => s.setHoveredHouse);
  const setVarga = useChartStore((s) => s.setVarga);
  const reduced = useReducedMotion() ?? false;

  const isRasi = activeVarga === "D1";
  const varga = useMemo(
    () => chart?.vargas.find((v) => v.code === activeVarga) ?? null,
    [chart, activeVarga],
  );

  const byHouse = useMemo(() => selectPlanetsByHouse(chart), [chart]);

  const vargaByHouse = useMemo(() => {
    const map = new Map<number, VargaPosition[]>();
    if (!varga) return map;
    for (const pos of varga.positions) {
      const list = map.get(pos.house) ?? [];
      list.push(pos);
      map.set(pos.house, list);
    }
    return map;
  }, [varga]);

  const active = useMemo(
    () => chart?.planets.find((p) => p.id === activePlanet) ?? null,
    [chart, activePlanet],
  );

  const rays = useMemo(() => {
    if (!chart || !active || !isRasi) return [];
    const asc = chart.ascendant.sign_index;
    const from = cellCenter(active.sign_index);
    const build = (houses: number[], disputed: boolean) =>
      houses.map((house) => ({
        house,
        disputed,
        d: drishtiPath(from, cellCenter(signForHouse(house, asc))),
      }));
    return [
      ...build(active.aspects_hitting, false),
      ...build(active.aspects_hitting_disputed, true),
    ];
  }, [chart, active, isRasi]);

  const litHouses = useMemo(
    () => new Set(active && isRasi ? [...active.aspects_hitting, active.house_index] : []),
    [active, isRasi],
  );

  if (!chart) return null;
  const asc = isRasi
    ? chart.ascendant.sign_index
    : (varga?.ascendant_sign_index ?? chart.ascendant.sign_index);
  const vargottamaCount = varga?.positions.filter((p) => p.vargottama).length ?? 0;

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="heading text-xl">
          {isRasi ? "Rasi" : varga?.name} &middot; {activeVarga}
        </h2>
        <span className="eyebrow">
          {isRasi
            ? active
              ? `${active.name} drishti`
              : "click a graha to trace its drishti"
            : varga?.read_for}
        </span>
      </div>

      {/* Division selector — all sixteen vargas. */}
      <div className="border-b border-slate-200/90 px-6 py-3">
        <div className="flex flex-wrap gap-1.5">
          {chart.vargas.map((v) => (
            <button
              key={v.code}
              type="button"
              onClick={() => setVarga(v.code)}
              title={`${v.name}: ${v.read_for}`}
              aria-pressed={v.code === activeVarga}
              className={`rounded-lg border px-2.5 py-1 font-mono text-micro font-bold transition-all ${
                v.code === activeVarga
                  ? "border-gold bg-gold-wash text-gold shadow-sm"
                  : "border-slate-300 bg-white text-ink-2 hover:border-slate-400 hover:bg-wash"
              }`}
            >
              {v.code}
            </button>
          ))}
        </div>
      </div>

      <div className="panel-body">
        {!isRasi && varga && (
          <div className="mb-4 rounded-xl border border-slate-200/90 bg-wash px-4 py-3">
            <p className="text-meta text-ink">
              <span className="font-semibold">
                {varga.name} ({varga.code})
              </span>{" "}
              divides each sign into {varga.divisions}. Read for {varga.read_for}.
              Ascendant {varga.ascendant_sign}.
              {vargottamaCount > 0 && (
                <>
                  {" "}
                  <span className="text-gold">{vargottamaCount} vargottama</span>,
                  holding the same sign as in D1.
                </>
              )}
            </p>
            {varga.note && (
              <p className="mt-2 text-meta italic text-ink-2">{varga.note}</p>
            )}
            <p className="mt-2 text-meta text-ink-2">
              Divisions carry placement, not degrees, and drishti is computed in
              the rasi, so aspect tracing is offered in D1 only.
            </p>
          </div>
        )}

        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="mx-auto block h-auto w-full max-w-[560px]"
          role="img"
          aria-label={`South Indian ${activeVarga} chart`}
        >
          <defs>
            <linearGradient id="rayGold" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={CHART.goldBright} stopOpacity="0.25" />
              <stop offset="50%" stopColor={CHART.gold} stopOpacity="0.95" />
              <stop offset="100%" stopColor={CHART.nebula} stopOpacity="0.6" />
            </linearGradient>
          </defs>

          {Array.from({ length: 12 }, (_, signIndex) => {
            const { col, row } = cellFor(signIndex);
            const house = houseForSign(signIndex, asc);
            const x = col * CELL;
            const y = row * CELL;
            const planets = byHouse.get(house) ?? [];
            const vargaCell = vargaByHouse.get(house) ?? [];
            const isHovered = hoveredHouse === house;
            const isLagna = house === 1;
            const isSoothed = soothed.includes(house);
            const faded = Boolean(active) && isRasi && !litHouses.has(house);
            const sav =
              chart.houses.find((h) => h.house === house)?.sarvashtakavarga ?? 0;

            return (
              <g
                key={signIndex}
                onMouseEnter={() => setHoveredHouse(house)}
                onMouseLeave={() => setHoveredHouse(null)}
              >
                <motion.rect
                  x={x + 1.5}
                  y={y + 1.5}
                  width={CELL - 3}
                  height={CELL - 3}
                  rx={7}
                  fill={
                    isSoothed
                      ? CHART.cellSoothed
                      : isHovered
                        ? CHART.cellHover
                        : (signIndex + Math.floor(signIndex / 4)) % 2 === 0
                          ? CHART.cell
                          : CHART.cellAlt
                  }
                  stroke={
                    isHovered
                      ? CHART.goldBright
                      : isSoothed
                        ? CHART.nebulaBright
                        : isLagna
                          ? CHART.gold
                          : CHART.stroke
                  }
                  strokeWidth={isHovered || isLagna ? 2.2 : 1.2}
                  animate={{ opacity: faded ? 0.45 : 1 }}
                  transition={{ duration: 0.28 }}
                />

                <text
                  x={x + 12}
                  y={y + 22}
                  fontSize={CHART_TYPE.sign}
                  fontWeight={500}
                  fill={CHART.ink3}
                  style={{ fontFamily: "var(--font-mono), monospace" }}
                >
                  {SIGN_ABBR[signIndex] ?? ""}
                </text>

                {/* House number sits in its own tinted pill so it never reads
                    as one of the planetary figures below it. */}
                <rect
                  x={x + CELL - (isLagna ? 46 : 32)}
                  y={y + 9}
                  width={isLagna ? 34 : 20}
                  height={19}
                  rx={5}
                  fill={isLagna ? CHART.goldWash : CHART.wash}
                  stroke={isLagna ? CHART.goldBright : CHART.hairStrong}
                  strokeWidth={0.9}
                />
                <text
                  x={x + CELL - 22}
                  y={y + 23}
                  fontSize={CHART_TYPE.house}
                  fontWeight={700}
                  textAnchor="middle"
                  fill={isLagna ? CHART.gold : CHART.ink2}
                  style={{ fontFamily: "var(--font-mono), monospace" }}
                >
                  {isLagna ? "ASC" : house}
                </text>

                {isRasi && (
                  <text
                    x={x + CELL - 12}
                    y={y + CELL - 11}
                    fontSize={CHART_TYPE.sav}
                    fontWeight={500}
                    textAnchor="end"
                    fill={CHART.ink3}
                    style={{ fontFamily: "var(--font-mono), monospace" }}
                  >
                    {sav}
                  </text>
                )}

                <g transform={`translate(${x + 16}, ${y + 52})`}>
                  {isRasi
                    ? planets.map((p, i) => (
                        <g key={p.id} transform={`translate(0, ${i * 23})`}>
                          <PlanetGlyph
                            planet={p}
                            index={i}
                            faded={faded}
                            reduced={reduced}
                            active={p.id === activePlanet}
                            onSelect={setActivePlanet}
                          />
                        </g>
                      ))
                    : vargaCell.map((pos, i) => (
                        <g key={pos.name} transform={`translate(0, ${i * 21})`}>
                          <VargaGlyph position={pos} index={i} reduced={reduced} />
                        </g>
                      ))}
                </g>
              </g>
            );
          })}

          <AnimatePresence>
            {rays.map((r) => (
              <motion.path
                key={`${activePlanet}-${r.house}-${r.disputed}`}
                d={r.d}
                fill="none"
                stroke={r.disputed ? CHART.nebulaBright : "url(#rayGold)"}
                strokeWidth={r.disputed ? 1.4 : 2.2}
                strokeDasharray={r.disputed ? "4 5" : undefined}
                strokeLinecap="round"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                exit={{ pathLength: 0, opacity: 0 }}
                transition={{ duration: reduced ? 0 : 0.75, ease: "easeInOut" }}
              />
            ))}
          </AnimatePresence>

          <g transform={`translate(${CENTER}, ${CENTER})`}>
            <text
              textAnchor="middle"
              y={-14}
              fontSize={CHART_TYPE.centreLabel}
              fontWeight={600}
              fill={CHART.ink2}
              style={{
                fontFamily: "var(--font-mono), monospace",
                letterSpacing: "0.1em",
              }}
            >
              {isRasi
                ? active
                  ? active.name.toUpperCase()
                  : chart.ascendant.sign.toUpperCase()
                : activeVarga}
            </text>
            <text
              textAnchor="middle"
              y={12}
              fontSize={CHART_TYPE.centreValue}
              fontWeight={700}
              fill={CHART.gold}
              style={{ fontFamily: "var(--font-mono), monospace" }}
            >
              {isRasi
                ? active
                  ? active.degree_dms
                  : chart.ascendant.degree_dms
                : (varga?.ascendant_sign ?? "")}
            </text>
            <text
              textAnchor="middle"
              y={35}
              fontSize={CHART_TYPE.centreNak}
              fontWeight={500}
              fill={CHART.ink2}
              style={{ fontFamily: "var(--font-mono), monospace" }}
            >
              {isRasi
                ? active
                  ? `${active.nakshatra} ${active.pada}`
                  : `${chart.ascendant.nakshatra} ${chart.ascendant.pada}`
                : `lagna ${varga?.ascendant_sign ?? ""}`}
            </text>
          </g>
        </svg>

        {isRasi && active && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 space-y-3 border-t border-slate-200/90 pt-5"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="chip chip-gold">{active.dignity}</span>
              {active.retrograde && <span className="chip chip-neg">retrograde</span>}
              {active.combust && <span className="chip chip-neg">combust</span>}
              {active.sandhi && <span className="chip chip-nebula">sandhi</span>}
              <span className="chip chip-muted">{active.functional}</span>
              {active.shadbala_rupas !== null && (
                <span className="chip chip-muted">
                  {active.shadbala_rupas.toFixed(2)} rupas
                </span>
              )}
            </div>
            <p className="text-meta leading-relaxed text-ink-2">
              {active.dignity_why}. In {active.nakshatra} pada {active.pada}, whose
              lord is {active.nakshatra_lord} and whose deity is{" "}
              {active.nakshatra_deity}. Navamsa {active.navamsa_sign}.
            </p>
            {active.aspects_hitting_disputed.length > 0 && (
              <p className="text-meta text-nebula">
                Dashed rays are nodal aspects, which BPHS does not grant. Shown, but
                never counted as evidence.
              </p>
            )}
          </motion.div>
        )}
      </div>
    </section>
  );
}
