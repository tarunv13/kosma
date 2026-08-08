/**
 * Chart palette and type scale, in one place.
 *
 * SVG fill/stroke attributes cannot read Tailwind classes, so the values the
 * chart draws with live here. These mirror `tailwind.config.ts`; changing a
 * colour means changing both, which is the cost of drawing in SVG.
 *
 * Contrast against the white cell, measured:
 *   ink   #0F172A  17.0:1    ink2 #334155  10.3:1
 *   ink3  #475569   7.4:1    gold #6B4708   8.3:1
 *   neg   #8F1E16   8.9:1    nebula #5B2E9D 9.1:1
 * ink4 is deliberately absent — it is a stroke colour, never type.
 */
export const CHART = {
  ink: "#0F172A",
  ink2: "#334155",
  ink3: "#475569",

  hair: "#E2E8F0",
  hairStrong: "#CBD5E1",
  stroke: "#94A3B8", // non-text strokes only

  gold: "#6B4708",
  goldBright: "#D8A33C",
  goldWash: "#FDF6E7",

  nebula: "#5B2E9D",
  nebulaBright: "#8B5CD6",
  nebulaWash: "#F3EDFC",

  pos: "#0F5233",
  neg: "#8F1E16",

  wash: "#F1F5F9", // house-number pill ground
  cell: "#FFFFFF",
  cellAlt: "#F8FAFC",
  cellHover: "#FDF6E7",
  cellSoothed: "#F3EDFC",
} as const;

/**
 * Type sizes inside the chart SVG, in viewBox units.
 *
 * The SVG renders at roughly 0.93 scale in a five-column layout, so each of
 * these lands about 7% smaller on screen — the values are set with that
 * shrinkage already accounted for rather than being nominal.
 */
export const CHART_TYPE = {
  glyph: 17, // planet code, e.g. "Ma℞"
  degree: 15, // "14.94°"
  house: 14, // house number / ASC
  sign: 13.5, // "Gem"
  sav: 12.5, // sarvashtakavarga
  centreLabel: 14,
  centreValue: 21,
  centreNak: 13.5,
} as const;
