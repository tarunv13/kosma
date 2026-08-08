"use client";

import type { House } from "@/types/chart";

/**
 * Everything the engine knows about one bhava, laid out for a reader.
 *
 * The order answers the questions a person actually asks, in the order they
 * ask them: what is this house about, what sign is on it, who rules it and
 * where did that ruler go, who is sitting here, what is looking at this house,
 * how well supplied is it, and is any of it live right now.
 *
 * Note what is absent. There is no generated narrative — no "this means you
 * will…". The panel states classical signification and computed structure and
 * stops. Turning that into prose about a particular life is the interpretation
 * layer's job, and it only gets to do it for topics the gate passed.
 */

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-[7.5rem_1fr] gap-x-4 gap-y-1 border-b border-slate-200/70 py-2.5 last:border-0">
      <dt className="eyebrow pt-0.5">{label}</dt>
      <dd className="text-meta leading-relaxed text-ink-2">{children}</dd>
    </div>
  );
}

export default function HouseDossier({ house }: { house: House }) {
  const lp = house.lord_placement;
  const benefics = house.aspects_received.filter((a) => a.benefic && !a.disputed);
  const malefics = house.aspects_received.filter((a) => !a.benefic && !a.disputed);
  const nodal = house.aspects_received.filter((a) => a.disputed);

  const savTone =
    house.sarvashtakavarga_band === "well supplied"
      ? "text-pos"
      : house.sarvashtakavarga_band === "thinly supplied"
        ? "text-neg"
        : "text-ink-2";

  return (
    <div className="rounded-xl border border-slate-200/90 bg-wash p-5">
      <p className="mb-4 text-base leading-relaxed text-ink">{house.governs}</p>

      <dl>
        <Row label="Sign">
          <span className="font-mono font-semibold text-ink">{house.sign}</span> sits
          on the {house.house === 1 ? "ascendant" : `${house.house}th cusp`}.
        </Row>

        <Row label="Lord">
          <span className="font-mono font-semibold text-ink">{house.lord}</span> rules
          it and sits in the{" "}
          <span className="font-mono font-semibold text-ink">
            {lp.in_house}
            {lp.in_house === 1 ? "st" : lp.in_house === 2 ? "nd" : lp.in_house === 3 ? "rd" : "th"}
          </span>{" "}
          house, in {lp.in_sign} {lp.degree_dms}
          {lp.retrograde && <span className="text-neg"> · retrograde</span>}
          {lp.combust && <span className="text-neg"> · combust</span>}.
          <span className="mt-1 block text-ink-3">{lp.dignity_why}.</span>
        </Row>

        <Row label="Occupants">
          {house.occupants.length === 0 ? (
            <span className="text-ink-3">
              Empty. Classical practice reads an empty house through its lord and
              the grahas aspecting it, which is what the rows above and below do.
            </span>
          ) : (
            <ul className="space-y-2">
              {house.occupants.map((o) => (
                <li key={o.name}>
                  <span className="font-mono font-semibold text-ink">{o.name}</span>{" "}
                  <span className="font-mono text-ink-3">{o.degree_dms}</span> ·{" "}
                  {o.nakshatra} pada {o.pada}
                  {o.retrograde && <span className="text-neg"> · retrograde</span>}
                  {o.combust && <span className="text-neg"> · combust</span>}
                  <span className="mt-0.5 block text-ink-3">
                    {o.dignity}, functionally {o.functional}.
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Row>

        <Row label="Drishti">
          {benefics.length === 0 && malefics.length === 0 ? (
            <span className="text-ink-3">No graha aspects this house.</span>
          ) : (
            <>
              {benefics.length > 0 && (
                <span>
                  <span className="text-pos">Benefic:</span>{" "}
                  <span className="font-mono">
                    {benefics.map((a) => a.planet).join(", ")}
                  </span>
                  .{" "}
                </span>
              )}
              {malefics.length > 0 && (
                <span>
                  <span className="text-neg">Malefic:</span>{" "}
                  <span className="font-mono">
                    {malefics.map((a) => a.planet).join(", ")}
                  </span>
                  .
                </span>
              )}
              {nodal.length > 0 && (
                <span className="mt-1 block text-nebula">
                  {nodal.map((a) => a.planet).join(", ")} also aspect it under
                  schools that grant the nodes drishti; BPHS does not, so this is
                  shown but not counted.
                </span>
              )}
            </>
          )}
        </Row>

        <Row label="Strength">
          <span className={`font-mono font-semibold ${savTone}`}>
            {house.sarvashtakavarga} bindus
          </span>{" "}
          — {house.sarvashtakavarga_band}. Out of 337 across the chart; 30 or more
          counts as strong, 25 or fewer as thin.
        </Row>

        <Row label="Karaka">
          <span className="font-mono font-semibold text-ink">{house.karaka}</span> is
          the natural significator, itself in {house.karaka_placement.in_sign}, house{" "}
          {house.karaka_placement.in_house}, {house.karaka_placement.dignity}.
          <span className="mt-1 block text-ink-3">{house.karaka_note}</span>
        </Row>

        {house.currently_active.length > 0 && (
          <Row label="Live now">
            <span className="text-gold">
              {house.currently_active.join("; ")}.
            </span>
            <span className="mt-1 block text-ink-3">
              A running period marks the theme as active. It does not schedule an
              event.
            </span>
          </Row>
        )}
      </dl>
    </div>
  );
}
