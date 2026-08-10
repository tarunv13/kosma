/**
 * The wire contract, typed.
 *
 * This mirrors `kosma/api_contract.py` field for field. The two files are the
 * same contract written twice, on purpose: `CONTRACT_VERSION` is checked at
 * runtime so a stale client fails loudly instead of rendering nonsense.
 */

export const SUPPORTED_CONTRACT = "1.3";

export interface ChartMeta {
  generator: string;
  ayanamsa: string;
  ayanamsa_value: number;
  zodiac: "sidereal";
  house_system: string;
  location: { lat: number; lon: number; tz: number; label: string };
  datetime: string;
  computed_at: string;
  subject: string | null;
}

export interface Ascendant {
  sign: string;
  sign_index: number;
  long: number;
  degree: number;
  degree_dms: string;
  nakshatra: string;
  pada: number;
  lord: string;
}

/** What the tradition holds one graha in one bhava to mean, for this chart. */
export interface PlacementReading {
  planet: string;
  sanskrit: string;
  house: number;
  sign: string;
  dignity: string;
  /** kendra / trikona / dusthana / upachaya, as applicable. */
  classes: string[];
  signifies: string;
  strengths: string;
  weaknesses: string;
  /** How the placement colours the person. */
  nature: string;
  class_note: string;
  /** A classical particular, where one exists. Empty otherwise. */
  notable: string;
  /** What this chart's dignity, retrogression and combustion do to the above. */
  condition: string;
  remedy: {
    graha: string;
    mantra: string;
    transliteration: string;
    gem: string;
    daana: string;
    vara: string;
    practical: string;
    caveat: string;
    ratna_caveat: string;
  };
}

export interface Planet {
  id: string;
  name: string;
  /** Two-letter abbreviation. Always renders, in any font. */
  glyph: string;
  /** The astronomical symbol, shown with the abbreviation as its label. */
  symbol: string;
  placement: PlacementReading;
  /** Absolute sidereal longitude, 0–360. */
  long: number;
  /** Degrees per day; negative means retrograde. */
  speed: number;
  /** Degrees within the sign. */
  degree: number;
  degree_dms: string;
  sign: string;
  sign_index: number;
  house_index: number;
  nakshatra: string;
  pada: number;
  nakshatra_lord: string;
  nakshatra_deity: string;
  retrograde: boolean;
  combust: boolean;
  /** Within one degree of a sign boundary. */
  sandhi: boolean;
  dignity: string;
  dignity_why: string;
  functional: string;
  benefic: boolean;
  /** Houses this planet aspects under Parashari drishti. */
  aspects_hitting: number[];
  /** Nodal aspects, which BPHS does not grant. Rendered differently. */
  aspects_hitting_disputed: number[];
  navamsa_sign: string;
  shadbala_rupas: number | null;
  shadbala_band: string | null;
}

export interface Occupant {
  name: string;
  glyph: string;
  symbol: string;
  degree_dms: string;
  nakshatra: string;
  pada: number;
  dignity: string;
  dignity_why: string;
  retrograde: boolean;
  combust: boolean;
  benefic: boolean;
  functional: string;
}

export interface AspectReceived {
  planet: string;
  rule: string;
  benefic: boolean;
  disputed: boolean;
}

export interface Placement {
  in_house: number;
  in_sign: string;
  degree_dms?: string;
  nakshatra?: string;
  dignity: string;
  dignity_why?: string;
  functional?: string;
  retrograde?: boolean;
  combust?: boolean;
}

/** The full structural dossier for one bhava. */
export interface House {
  house: number;
  sign: string;
  sign_index: number;
  topic: string;
  /** Classical significations, condensed. Reference, not prediction. */
  governs: string;
  lord: string;
  lord_placement: Placement;
  occupants: Occupant[];
  aspects_received: AspectReceived[];
  sarvashtakavarga: number;
  sarvashtakavarga_band: string;
  karaka: string;
  karaka_note: string;
  karaka_placement: Placement;
  /** Non-empty when a dasha lord rules or occupies this house right now. */
  currently_active: string[];
}

export interface VargaPosition {
  name: string;
  glyph: string;
  sign: string;
  sign_index: number;
  house: number;
  lord: string;
  /** Same sign in this division as in D1 — a classical strength marker. */
  vargottama: boolean;
}

export interface Varga {
  code: string;
  name: string;
  divisions: number;
  read_for: string;
  note: string | null;
  ascendant_sign: string;
  ascendant_sign_index: number;
  positions: VargaPosition[];
}

export interface Yoga {
  name: string;
  planets: string[];
  houses: number[];
  detail: string;
  rule: string;
  source: string;
  /** +1 auspicious, -1 challenging, 0 mixed. */
  polarity: number;
  caveat: string | null;
  disputed: boolean;
}

export interface DashaPeriod {
  lord: string;
  from: string;
  to: string;
  from_jd: number;
  to_jd: number;
  status: "past" | "active" | "upcoming";
  children?: DashaPeriod[];
}

export interface Dashas {
  current: {
    mahadasha: string | null;
    antardasha: string | null;
    pratyantardasha: string | null;
  };
  timeline: DashaPeriod[];
}

/**
 * The same finding said in ordinary English.
 *
 * Built server-side from the very evidence entries the finding cites, so it
 * cannot describe a chart the ledger does not support. The technical fields
 * above it are not replaced -- they move one click away.
 */
export interface PlainReading {
  house: number;
  topic: string;
  /** The fuller description of the area of life this house covers. */
  governs: string;
  /** One sentence: the shape of this house's answer. */
  headline: string;
  /** Two or three sentences narrating the evidence. */
  body: string[];
  /** What this reading does not claim. */
  limit: string;
  /** The natural significator, and what reading it alongside adds. */
  karaka_note: string;
}

export interface Finding {
  house: number;
  topic: string;
  verdict: string;
  confidence: string;
  kinds: string[];
  citations: string[];
  plain: PlainReading;
}

export interface Withheld {
  house: number;
  topic: string;
  reason: string;
  plain: PlainReading;
}

export interface EvidenceItem {
  id: string;
  house: number;
  kind: string;
  statement: string;
  basis: string;
  source: string;
  polarity: number;
  disputed: boolean;
}

export interface Panchanga {
  vara: string;
  tithi: string;
  paksha: string;
  yoga: string;
  karana: string;
  moon_nakshatra: string;
}

export interface ChartResponse {
  contract_version: string;
  chart_meta: ChartMeta;
  ascendant: Ascendant;
  planets: Planet[];
  houses: House[];
  vargas: Varga[];
  panchanga: Panchanga;
  yogas: Yoga[];
  dashas: Dashas;
  findings: Finding[];
  withheld: Withheld[];
  evidence: EvidenceItem[];
  gate: { rule: string; minimum_agreeing_kinds: number };
  /** Term -> plain meaning, so jargon can be glossed where it appears. */
  glossary: Record<string, string>;
  /** Factor kind -> the plain name for it, e.g. "aspect" -> "planets looking at this house". */
  kind_labels: Record<string, string>;
  numerology: Numerology;
  gender: Gender;
  disclaimer: string;
}

export type Gender = "female" | "male" | "other" | "unspecified";

export interface NumberReading {
  number: number;
  /** The graha this number is tied to in Indian numerology. */
  graha: string;
  meaning: string;
  /** How this number was derived. Always stated. */
  method: string;
}

/**
 * Reported beside the chart, never inside it.
 *
 * Numerology casts no vote on any finding: the gate requires two independent
 * kinds of *chart* factor to agree, and a number from a date or a spelling is
 * not one. Both name systems are carried because they disagree, and choosing
 * one silently would hide that.
 */
export interface Numerology {
  mulank: NumberReading;
  bhagyank: NumberReading;
  name_chaldean: NumberReading | null;
  name_pythagorean: NumberReading | null;
  systems_agree: boolean | null;
  disagreement?: string;
  note: string;
  name_note: string;
}

export interface BirthInput {
  name: string;
  birth_date: string;
  birth_time: string;
  city: string;
  /**
   * Optional. Several kootas are stated in the classical texts as a rule
   * about the bride relative to the groom, so the two roles genuinely change
   * a compatibility score. Where it is not given the engine falls back to
   * entry order and says so, rather than assuming a role.
   */
  gender: Gender;
}

/** Fixed South Indian grid position for each sign index (0 = Aries). */
export const SOUTH_INDIAN_CELLS: Record<number, { col: number; row: number }> = {
  11: { col: 0, row: 0 }, //  Pisces
  0: { col: 1, row: 0 }, //   Aries
  1: { col: 2, row: 0 }, //   Taurus
  2: { col: 3, row: 0 }, //   Gemini
  3: { col: 3, row: 1 }, //   Cancer
  4: { col: 3, row: 2 }, //   Leo
  5: { col: 3, row: 3 }, //   Virgo
  6: { col: 2, row: 3 }, //   Libra
  7: { col: 1, row: 3 }, //   Scorpio
  8: { col: 0, row: 3 }, //   Sagittarius
  9: { col: 0, row: 2 }, //   Capricorn
  10: { col: 0, row: 1 }, //  Aquarius
};

export const SIGN_ABBR = [
  "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
  "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis",
];


/* ── Compatibility ──────────────────────────────────────────────────── */

export interface Koota {
  name: string;
  score: number;
  maximum: number;
  fraction: number;
  detail: string;
  rule: string;
  source: string;
  void: boolean;
  full: boolean;
  variant_note: string | null;
}

export interface Dosha {
  name: string;
  present: boolean;
  cancelled: boolean;
  status: string;
  detail: string;
  cancellations: string[];
  source: string;
  note: string;
}

export interface CompatFinding {
  topic: string;
  description: string;
  verdict: string;
  confidence: string;
  kinds: string[];
  citations: string[];
}

export interface CompatWithheld {
  topic: string;
  description: string;
  reason: string;
}

export interface Overlay {
  planet: string;
  house: number;
  theme: string;
  polarity: number;
}

export interface CrossAspect {
  from_person: string;
  planet: string;
  to_person: string;
  target: string;
  rule: string;
  polarity: number;
}

export interface PairReport {
  a: string;
  b: string;
  mode: string;
  findings: CompatFinding[];
  withheld: CompatWithheld[];
  milan: {
    scheme: string;
    total: number;
    maximum: number;
    percentage: number;
    critique: string;
    kootas: Koota[];
  };
  doshas: Dosha[];
  overlays: { a_into_b: Overlay[]; b_into_a: Overlay[] };
  cross_aspects: CrossAspect[];
  dasha_sync: {
    a_mahadasha: string | null;
    a_antardasha: string | null;
    b_mahadasha: string | null;
    b_antardasha: string | null;
    relation: string;
    shared: string[];
    detail: string;
  };
  evidence: EvidenceItem[];
  navamsa_note: string;
}

export interface CompatProfile {
  label: string;
  place: string;
  datetime: string;
  ascendant: string;
  ascendant_dms: string;
  moon_sign: string;
  moon_nakshatra: string;
  moon_pada: number;
}

export interface CompatibilityResponse {
  contract_version: string;
  mode: "relationship" | "friendship";
  computed_at: string;
  people: CompatProfile[];
  pairs: PairReport[];
  gate: { minimum_agreeing_kinds: number; factor_kinds: string[] };
  disclaimer: string;
}

export interface PersonInput {
  name: string;
  birth_date: string;
  birth_time: string;
  city: string;
}
